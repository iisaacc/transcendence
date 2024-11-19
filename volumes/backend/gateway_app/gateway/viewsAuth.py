import os, json, requests, logging, jwt
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .forms import SignUpFormFrontend, LogInFormFrontend
from .viewsProfile import get_profileapi_variables
from .utils import getDjangoLanguageCookie, getUserId
from .authmiddleware import generate_guest_token
from django.utils.translation import gettext as _
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta, timezone


logger = logging.getLogger(__name__)


# Logout

@login_required
def get_logout(request):
    authentif_url = 'https://authentif:9001/api/logout/' 
    
    # Only allow GET requests
    if request.method != 'GET':
        return redirect('405')
    
    # TODO => Temporary fix
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return redirect('home')

    try:
        # Make the external request to the authentif service
        response = requests.get(authentif_url, cookies=request.COOKIES, verify=os.getenv("CERTFILE"))
        
        json_response = JsonResponse({
              'status': 'success',
              'type': 'logout_successful',
              'message': _('Logged out successfully')
            })

        # Set cookies from the response into the JsonResponse
        for cookie_name, cookie_value in response.cookies.items():
            json_response.set_cookie(cookie_name, cookie_value)
        
        # Set headers from response
        for header_name, header_value in response.headers.items():
            # Avoid overwriting 'Content-Type' or 'Content-Length' as they are set by JsonResponse
            if header_name.lower() not in ['content-type', 'content-length']:
                json_response[header_name] = header_value
        
        # Return the response
        return json_response
    
    except requests.exceptions.RequestException as e:
      return JsonResponse({'status': 'error', 'message': _('Failed to log out')}, status=503)

# Login
def view_login(request):
    if request.user.is_authenticated:
      return redirect('home')
    if request.method == 'GET': 
       return get_login(request)      
    elif request.method == 'POST':
       return post_login(request=request)
    else:
      return redirect('405')

def get_login(request):
    form = LogInFormFrontend()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('fragments/login_fragment.html', {'form': form, 'CLIENT_ID': settings.CLIENT_ID, 'REDIRECT_URI': settings.REDIRECT_URI}, request=request)
        return JsonResponse({'html': html})
    return render(request, 'partials/login.html', {'form': form, 'CLIENT_ID': settings.CLIENT_ID, 'REDIRECT_URI': settings.REDIRECT_URI})
   
User = get_user_model()

def post_login(request):
    authentif_url = 'https://authentif:9001/api/login/'
    
    if request.method != 'POST':
        return redirect('405')

    csrf_token = request.COOKIES.get('csrftoken')
    jwt_token = request.COOKIES.get('jwt_token')
    django_language = getDjangoLanguageCookie(request)
    headers = {
        'X-CSRFToken': csrf_token,
        'X-Language': django_language,
        'Cookie': f'csrftoken={csrf_token}',
        'Content-Type': 'application/json',
        'Referer': 'https://gateway:8443',
        'Authorization': f'Bearer {jwt_token}',
    }
    
    data = json.loads(request.body)
    
    # Validate the form data
    form = LogInFormFrontend(data)
    if not form.is_valid():
        message = _("Invalid form data")
        form.add_error(None, message)
        html = render_to_string('fragments/login_fragment.html', {'form': form, 'CLIENT_ID': settings.CLIENT_ID, 'REDIRECT_URI': settings.REDIRECT_URI}, request=request)
        return JsonResponse({'html': html, 'status': 'error', 'message': message}, status=400)
    
    # Forward the request to the auth service
    try:
        response = requests.post(authentif_url, json=data, headers=headers, verify=os.getenv("CERTFILE"))
    except requests.exceptions.RequestException as e:
        return JsonResponse({'status': 'error', 'message': 'Authentication service unavailable'}, status=503)

    response_data = response.json()
    # Handle the response from the auth service
    if response.ok:
        # Extract token and message from the auth service
        jwt_token = response_data.get("token")
        user_id = response_data.get("user_id")
        message = response_data.get("message")
        type = response_data.get("type")
        # get refresh token cookie from response
        refresh_jwt_token = response.cookies.get('refresh_jwt_token')

        if type == "2FA":
            return JsonResponse(response.json())
        if jwt_token:
            user_response = JsonResponse({'status': 'success', 'type': type, 'message': message, 'user_id': user_id})
            profile_data = get_profileapi_variables(response=response)
            preferred_language = profile_data.get('preferred_language')
            # Set the preferred language of the user, HTTP-only cookie
            user_response.set_cookie('django_language', preferred_language, httponly=False, secure=True, samesite='Lax')
            # Set the JWT token in a secure, HTTP-only cookie
            user_response.set_cookie('jwt_token', jwt_token, httponly=True, secure=True, samesite='Lax')
            user_response.set_cookie('refresh_jwt_token', refresh_jwt_token, httponly=True, secure=True, samesite='Lax')            
            return user_response
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to retrieve token'}, status=500)
    
    else:
        message = response_data.get("message", "Login failed")
        status = response_data.get("status", "error")

        data = json.loads(request.body)
        form = LogInFormFrontend(data)
        form.add_error(None, message)

        html = render_to_string('fragments/login_fragment.html', {'form': form, 'CLIENT_ID': settings.CLIENT_ID, 'REDIRECT_URI': settings.REDIRECT_URI}, request=request)
        return JsonResponse({'html': html, 'status': status, 'message': message}, status=response.status_code)


# Signup
def view_signup(request):
    if request.user.is_authenticated:
      return redirect('home')
    if request.method == 'GET': 
       return get_signup(request)      
    elif request.method == 'POST':
       return post_signup(request)
    else:
      return redirect('405')

def get_signup(request):
    if request.method != 'GET':
      return redirect('405')
    
    form = SignUpFormFrontend()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('fragments/signup_fragment.html', {'form': form}, request=request)
        return JsonResponse({'html': html})
    return render(request, 'partials/signup.html', {'form': form})

def post_signup(request):
    authentif_url = 'https://authentif:9001/api/signup/' 
    if request.method != 'POST':
      return redirect('405')

    try:
      data = json.loads(request.body)
    except json.JSONDecodeError:
      return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    
    # Validate the form data
    form = SignUpFormFrontend(data)
    if not form.is_valid():
        message = _("Invalid form data")
        form.add_error(None, message)
        html = render_to_string('fragments/signup_fragment.html', {'form': form}, request=request)
        return JsonResponse({'html': html, 'status': 'error', 'message': message}, status=400)

    csrf_token = request.COOKIES.get('csrftoken')  # Get CSRF token from cookies
    jwt_token = request.COOKIES.get('jwt_token')
    django_language = getDjangoLanguageCookie(request)
    headers = {
        'X-CSRFToken': csrf_token,
        'X-Language': django_language,
        'Cookie': f'csrftoken={csrf_token}',
        'Content-Type': 'application/json',
        'Referer': 'https://gateway:8443',
        'Authorization': f'Bearer {jwt_token}',
    }
    
    response = requests.post(authentif_url, json=data, headers=headers, verify=os.getenv("CERTFILE"))

    response_data = response.json()
    status = response_data.get("status")
    message = response_data.get("message")
    jwt_token = response_data.get("token")
    user_id = response_data.get("user_id")
    type = response_data.get("type")
    refresh_jwt_token = response.cookies.get('refresh_jwt_token')

    if jwt_token:
        user_response = JsonResponse({'status': 'success', 'type': type, 'message': message, 'user_id': user_id})
        # Set the JWT token in a secure, HTTP-only cookie
        user_response.set_cookie('jwt_token', jwt_token, httponly=True, secure=True, samesite='Lax')
        user_response.set_cookie('refresh_jwt_token', refresh_jwt_token, httponly=True, secure=True, samesite='Lax')
        return user_response
    else:
        form.add_error(None, message)
        html = render_to_string('fragments/signup_fragment.html', {'form': form}, request=request)
        return JsonResponse({'html': html, 'status': 'error', 'message': message}, status=400)


@csrf_exempt
def oauth(request):
    authentif_url = 'https://authentif:9001/api/oauth/'
    
    if request.method != 'POST':
        return redirect('405')

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON data", status=400)

    # Get the 'code' and 'state' parameters from the parsed JSON data
    auth_code = data.get('code')

    # TODO - compare the states for preventing cross-site attacks
    state = data.get('state')
    if not auth_code:
        return HttpResponse("Authorization code is missing", status=400)

    try:
        # Set up the JSON data to send in the POST request to the external service
        payload = json.dumps({'code': auth_code})  # Convert the data to a JSON string
        csrf_token = request.COOKIES.get('csrftoken')
        jwt_token = request.COOKIES.get('jwt_token')
        django_language = getDjangoLanguageCookie(request)
        headers = {
          'X-CSRFToken': csrf_token,
          'X-Language': django_language,
          'Cookie': f'csrftoken={csrf_token}',
          'Content-Type': 'application/json',
          'Referer': 'https://gateway:8443',
          'Authorization': f'Bearer {jwt_token}',
        }
        # Make the POST request to the external authentif service
        response = requests.post(authentif_url, cookies=request.COOKIES,data=payload, headers=headers, verify=os.getenv("CERTFILE"))       
        response_data = response.json() if response.status_code == 200 else {}
        
        # Create a base JsonResponse with status and message
        json_response_data = {
            'status': 'success',
            'message': response_data.get("message", _("No message provided")),
            'user_id': response_data.get("user_id")
        }

        # Merge response_data into the JsonResponse data
        json_response_data.update(response_data)

        # Create JsonResponse
        json_response = JsonResponse(json_response_data)

        # Set cookies from the response into the JsonResponse
        for cookie_name, cookie_value in response.cookies.items():
            json_response.set_cookie(cookie_name, cookie_value)
        
        # Set headers from response
        for header_name, header_value in response.headers.items():
            # Avoid overwriting 'Content-Type' or 'Content-Length' as they are set by JsonResponse
            if header_name.lower() not in ['content-type', 'content-length']:
                json_response[header_name] = header_value
        
        if response.cookies.get('django_language') == None:
            profile_data = get_profileapi_variables(response=response)
            preferred_language = profile_data.get('preferred_language')
            json_response.set_cookie('django_language', preferred_language, httponly=False, secure=True, samesite='Lax')
        return json_response

    except requests.exceptions.RequestException as e:
        # Handle external request failure gracefully
        return JsonResponse({'status': 'error', 'message': _('Failed to login with 42')})


def oauth_callback(request):
    """
    Renders the OAuth callback page where the popup window will extract the 'code'
    and 'state' from the URL, then send it back to the parent window using postMessage.
    """
    return render(request, 'fragments/oauth_callback.html')

@login_required
def enable2FA_redir(request):
    authentif_url = 'https://authentif:9001/api/enable2FA/'

    csrf_token = request.COOKIES.get('csrftoken')
    jwt_token = request.COOKIES.get('jwt_token')
    django_language = getDjangoLanguageCookie(request)
    headers = {
        'X-CSRFToken': csrf_token,
        'X-Language': django_language,
        'Cookie': f'csrftoken={csrf_token}',
        'Content-Type': 'application/json',
        'Referer': 'https://gateway:8443',
        'Authorization': f'Bearer {jwt_token}',
    }
    response = requests.post(authentif_url, headers=headers, verify=os.getenv("CERTFILE"))
    data = response.json()

    html = render_to_string('fragments/2FA_enable_fragment.html', {'data': data}, request=request)
    return JsonResponse({'html': html, 'status': data.get('status'), 'message': data.get('message'), 'two_fa_enabled': data.get('two_fa_enabled')})

@login_required
def confirm2FA_redir(request):
    # Ensure this is a POST request
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": _("Invalid request method. Use POST.")}, status=405)

    # Extract the OTP code from the request body
    try:
        body = json.loads(request.body)
        otp_code = body.get("otp_code")
        if not otp_code:
            return JsonResponse({"status": "error", "message": _("OTP code is required")}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": _("Invalid JSON format")}, status=400)

    authentif_url = 'https://authentif:9001/api/confirm2FA/'

    csrf_token = request.COOKIES.get('csrftoken')
    jwt_token = request.COOKIES.get('jwt_token')
    django_language = getDjangoLanguageCookie(request)
    headers = {
        'X-CSRFToken': csrf_token,
        'X-Language': django_language,
        'Cookie': f'csrftoken={csrf_token}',
        'Content-Type': 'application/json',
        'Referer': 'https://gateway:8443',
        'Authorization': f'Bearer {jwt_token}',
    }

    # Prepare the payload to send
    payload = {
        'otp_code': otp_code
    }

    # Send POST request to the authentif service
    try:
        response = requests.post(authentif_url, headers=headers, json=payload, verify=os.getenv("CERTFILE"))
        response_data = response.json()
        return JsonResponse(response_data, status=response.status_code)  # Return the response from the authentif service
    except requests.exceptions.RequestException as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@login_required
def disable2FA_redir(request):
    authentif_url = 'https://authentif:9001/api/disable2FA/'

    csrf_token = request.COOKIES.get('csrftoken')
    jwt_token = request.COOKIES.get('jwt_token')
    django_language = getDjangoLanguageCookie(request)
    headers = {
        'X-CSRFToken': csrf_token,
        'X-Language': django_language,
        'Cookie': f'csrftoken={csrf_token}',
        'Content-Type': 'application/json',
        'Referer': 'https://gateway:8443',
        'Authorization': f'Bearer {jwt_token}',
    }
    response = requests.post(authentif_url, headers=headers, verify=os.getenv("CERTFILE"))

    return JsonResponse(response.json())


import os
import requests
from django.http import JsonResponse
from django.shortcuts import render
import json

def verify2FA_redir(request, user_id):
    if request.method == 'GET':
        return render(request, 'fragments/2FA_verify_fragment.html', {"USER_ID": user_id})
    elif request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Invalid request method. Use POST."}, status=405)

    authentif_url = f'https://authentif:9001/api/verify2FA/{user_id}/'

    csrf_token = request.COOKIES.get('csrftoken')
    jwt_token = request.COOKIES.get('jwt_token')
    django_language = getDjangoLanguageCookie(request)
    headers = {
        'X-CSRFToken': csrf_token,
        'X-Language': django_language,
        'Cookie': f'csrftoken={csrf_token}',
        'Content-Type': 'application/json',
        'Referer': 'https://gateway:8443',
        'Authorization': f'Bearer {jwt_token}',
    }
    
    payload = json.loads(request.body)
    otp_code = payload.get('otp_code')


    payload = {
        'otp_code': otp_code,
    }

    # Send the POST request with the same payload
    response = requests.post(authentif_url, headers=headers, json=payload, verify=os.getenv("CERTFILE"))

    json_response = JsonResponse(response.json())

    # Copy cookies from the response and add them to the JsonResponse
    for cookie_name, cookie_value in response.cookies.items():
        json_response.set_cookie(
            key=cookie_name,
            value=cookie_value,
            httponly=True,
            secure=True,
            samesite='Lax',
        )

    return json_response

def refresh_token(request):
    #get jwt cookie from request
    jwt_token = request.COOKIES.get('jwt_token')
    refresh_token = request.COOKIES.get('refresh_jwt_token')
    try:
        decoded_data = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
    except:
        json_response = JsonResponse({'status': 'success', 'message': 'Invalid refresh token. Returning guest token'}, status=200)
        jwt_token = generate_guest_token()
        json_response.set_cookie('jwt_token', jwt_token, httponly=True, secure=True, samesite='Lax')
        return json_response

    json_response = JsonResponse({'status': 'success', 'message': 'Token refreshed successfully'})
    if len(jwt_token) > 10:
        try:
            jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            json_response = JsonResponse({'status': 'success', 'message': 'Expired Token refreshed'})
            try:
                # Now decode without checking expiry
                decoded_data = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
                user_id = decoded_data.get('user_id')
                if user_id == 0:
                    jwt_token = generate_guest_token()
                else:
                        access_exp = datetime.now(timezone.utc) + timedelta(minutes=1)  # Short-lived
                        access_payload = {
                            'user_id': user_id,
                            'exp': int(access_exp.timestamp()),
                            'iat': int(datetime.now(timezone.utc).timestamp()),
                        }
                        jwt_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256")
            except:
                return json_response


            # Filter and copy relevant cookies from the request to the response
            cookie_name = 'jwt_token'
            if cookie_name in request.COOKIES:
                json_response.set_cookie(
                    key="jwt_token",
                    value=jwt_token,
                    httponly=True,  # Helps mitigate XSS
                    secure=True,    # Requires HTTPS
                    samesite='Lax', # Helps mitigate CSRF
                )

    return json_response

async def get_user_id(request):
    jwt_token = request.COOKIES.get('jwt_token')
    if not jwt_token:
        return JsonResponse({'status': 'error', 'message': 'No JWT token found'}, status=400)

    try:
        user_id = await getUserId(jwt_token)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'success', 'user_id': user_id})

