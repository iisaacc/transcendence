import os, logging, jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta, timezone
from django.http import JsonResponse
from functools import wraps
from django.shortcuts import render

logger = logging.getLogger(__name__)

# In-memory blacklist for refresh tokens
blacklisted_refresh_tokens = {}

User = get_user_model()


def get_user_id(token):
    try:
        decoded_data = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        return decoded_data.get('user_id')
    except:
        return None


class GuestUser:
    def __init__(self):
        self.id = 0
        self.is_authenticated = False

    def __str__(self):
        return 'Guest User'


def generate_guest_token():
    guest_payload = {
        'user_id': 0,
        'exp': int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()),
        'iat': int(datetime.now(timezone.utc).timestamp()),
        'role': 'guest'
    }
    return jwt.encode(guest_payload, settings.SECRET_KEY, algorithm='HS256')


def generate_jwt_token(user):
    access_exp = datetime.now(timezone.utc) + timedelta(minutes=1)  # Short-lived
    refresh_exp = datetime.now(timezone.utc) + timedelta(days=7)    # Long-lived

    access_payload = {
        'user_id': user.id,
        'exp': int(access_exp.timestamp()),
        'iat': int(datetime.now(timezone.utc).timestamp()),
    }
    refresh_payload = {
        'user_id': user.id,
        'exp': int(refresh_exp.timestamp()),
        'iat': int(datetime.now(timezone.utc).timestamp()),
        'type': 'refresh'
    }

    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')

    return access_token, refresh_token


class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        self.process_response(request, response)
        return response

    def process_request(self, request):
        auth_header = request.headers.get('Authorization')
        access_token = request.COOKIES.get('jwt_token')
        refresh_token = request.COOKIES.get('refresh_jwt_token')
        header_token = auth_header.split('Bearer ')[1] if auth_header and auth_header.startswith('Bearer ') else None

        token = access_token if access_token else header_token

        if not token:
            request.user = self.create_guest_user()
            return

        if self.is_token_blacklisted(refresh_token):
            request.user = self.create_guest_user()
            return

        try:
            decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_data.get('user_id')
            user = User.objects.get(pk=user_id)
            request.user = user
        except (InvalidTokenError, User.DoesNotExist):
            request.user = self.create_guest_user()
        if refresh_token and request.path == '/api/refresh-token/':
            try:
                refresh_data = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
                user_id = refresh_data.get('user_id')
                user = User.objects.get(pk=user_id)

                new_access_token, new_refresh_token = generate_jwt_token(user)
                request.new_access_token = new_access_token
                request.new_refresh_token = new_refresh_token
                request.user = user
            except (ExpiredSignatureError, InvalidTokenError, User.DoesNotExist):
                request.user = self.create_guest_user()

    def process_response(self, request, response):
        self.cleanup_blacklisted_tokens()

        # Set new tokens if they were refreshed
        if hasattr(request, 'new_access_token') and hasattr(request, 'new_refresh_token'):
            response.set_cookie('jwt_token', request.new_access_token, httponly=True, secure=True, samesite='Lax')

        self.verify_or_generate_guest_token(request, response)
        return response

    def verify_or_generate_guest_token(self, request, response):
        access_token = request.COOKIES.get('jwt_token')
        if isinstance(request.user, GuestUser) or not request.user.is_authenticated:
            if not access_token:
                guest_token = generate_guest_token()
                response.set_cookie('jwt_token', guest_token, httponly=True, secure=True, samesite='Lax')

    def create_guest_user(self):
        return GuestUser()

    def is_token_blacklisted(self, refresh_token):
        return refresh_token in blacklisted_refresh_tokens and blacklisted_refresh_tokens[refresh_token] > datetime.now(timezone.utc)

    @staticmethod
    def blacklist_token(refresh_token):
        blacklisted_refresh_tokens[refresh_token] = datetime.now(timezone.utc)

    @staticmethod
    def cleanup_blacklisted_tokens():
        current_time = int(datetime.now(timezone.utc).timestamp())
        tokens_to_remove = [token for token, exp in blacklisted_refresh_tokens.items() if int(exp.timestamp()) < current_time]
        for token in tokens_to_remove:
            del blacklisted_refresh_tokens[token]


def login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # If user is not authenticated, respond with an error
        if not request.user.is_authenticated:
            return render(request, 'partials/401.html', status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped_view