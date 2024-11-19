import os, json, requests, logging, jwt
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import activate, gettext as _
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta, timezone
from .forms import SignUpForm, LogInForm, EditProfileForm
from .models import User
from .authmiddleware import login_required, generate_guest_token, JWTAuthenticationMiddleware, generate_jwt_token, get_user_id
import pyotp
import qrcode
from io import BytesIO
import base64
from django.core.cache import cache
import prettyprinter
prettyprinter.set_default_config(depth=None, width=80, ribbon_width=80)

logger = logging.getLogger(__name__)


def api_get_user_info(request, user_id):
    logger.debug("api_get_user_info")
    try:
        users = User.objects.all()
        users_id = [user.id for user in users]
        user = User.objects.get(id=user_id)
        if user:
            username = user.username
            avatar_url = user.avatar.url if user.avatar else None
            return JsonResponse({
                  'status': 'success',
                  'message': 'User found',
                  'username': username,
                  'usernames': [user.username for user in users],
                  'users_id': users_id,
                  'avatar_url': avatar_url
                })
        else:
            return JsonResponse({'status': 'error', 'message': _('User not found')}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': _('User not found')}, status=404)
        
@login_required
def api_logout(request):
    """Logs out the user by blacklisting their JWT token and sending a guest token."""
    token = request.COOKIES.get('jwt_token')
    refresh_token = request.COOKIES.get('refresh_jwt_token')

    if token:
        # Blacklist the current JWT token
        JWTAuthenticationMiddleware.blacklist_token(token)
        JWTAuthenticationMiddleware.blacklist_token(refresh_token)

        # Generate a new guest token
        guest_token = ""

        # Create a response indicating logout success
        response = JsonResponse({
              'status': 'success',
              'type': 'logout_successful',
              'message': _('Logged out successfully')
            })

        # Set the new guest JWT token as a cookie in the response
        response.set_cookie('jwt_token', guest_token, httponly=True, secure=True, samesite='Lax')
        response.set_cookie('refresh_jwt_token', guest_token, httponly=True, secure=True, samesite='Lax')

        return response
    else:
        return JsonResponse({'error': _('No active session found')}, status=400)
    
def api_login(request):
    logger.debug("api_login")
    # logger.debug(f"api_login > request.headers: {pformat(request.headers)}")
    language = request.headers.get('X-Language', 'en')
    activate(language)
    try:
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                form = LogInForm(request, data=data)
                try:
                    if form.is_valid():
                        user = form.get_user()
                        try:
                            login(request, user)
                        except Exception as e:
                            logger.error(f'api_login > Failed to log in user: {e}')
                            return JsonResponse({'status': 'error', 'message': _('Wrong credentials')}, status=401)
                        
                        logger.debug(f"api_login > User.id: {user.id}")

                        if user.two_factor_token:
                            auth_header = request.META.get('HTTP_AUTHORIZATION')

                            if auth_header and auth_header.startswith('Bearer '):
                                token = auth_header.split(' ')[1]  # Get the token part after 'Bearer '
                                
                                # Set the token in the cache
                                cache_key = f"2fa_user_{user.id}"
                                cache.set(cache_key, token, timeout=60*5)  # Cache for 5 minutes
                            return JsonResponse({'status': 'success', 'message': _('2FA required'), 'user_id': user.id, 'type': '2FA'}, status=200)

                        # Generate a JWT token for the authenticated user
                        jwt_token, refresh_jwt_token = generate_jwt_token(user)
                        logger.debug(f"token >>>>>>>>>>>: {jwt_token}")

                        # Create response object
                        response = JsonResponse({
                            'status': 'success',
                            'type': 'login_successful',
                            'message': _('Login successful'),
                            'token': jwt_token,
                            'user_id': user.id
                        })

                        # Set the JWT token in the headers and a secure cookie
                        response['Authorization'] = f'Bearer {jwt_token}'
                        response.set_cookie(
                            key='jwt_token',
                            value=jwt_token,
                            httponly=True,
                            secure=True,
                            samesite='Lax',
                            max_age=60 * 60 * 24 * 7,
                        )
                        response.set_cookie(
                            key='refresh_jwt_token',
                            value=refresh_jwt_token,
                            httponly=True,
                            secure=True,
                            samesite='Lax',
                            max_age=60 * 60 * 24 * 7,
                        )
                        
                        return response

                    else:
                        logger.debug('api_login > Invalid username or password')
                        return JsonResponse({'status': 'error', 'message': _('Invalid username or password')}, status=401)
                except:
                    logger.debug(f'Password validation error: {e.messages}')
                    return JsonResponse({'status': 'error', 'message': _('Wrong credentials')}, status=401)
            except json.JSONDecodeError:
                logger.debug('api_login > Invalid JSON')
                return JsonResponse({'status': 'error', 'message': _('Invalid JSON')}, status=400)
    except:
        logger.debug('api_login > Wrong or invalid password')
        return JsonResponse({'status': 'error', 'message': _('Wrong or invalid password')}, status=400)
    logger.debug('api_login > Method not allowed')
    return JsonResponse({'status': 'error', 'message': _('Method not allowed')}, status=405)

# Create a profile linked to user through call to profileapi service
def createProfile(username, user_id, csrf_token, id_42, lang):
    profileapi_url = 'https://profileapi:9002/api/signup/'
    if id_42:
        profile_data = { 'user_id': user_id, 'username': username, 'id_42': id_42 }
    else:
        profile_data = { 'user_id': user_id, 'username': username }
    
    headers = {
        'X-CSRFToken': csrf_token,
        'X-Language': lang,
        'Cookie': f'csrftoken={csrf_token}',
        'Content-Type': 'application/json',
        'HTTP_HOST': 'profileapi',
        'Referer': 'https://authentif:9001',
    }

    cookies = {
    'csrftoken': f'{csrf_token}',
    }

    try:
        response = requests.post(profileapi_url, json=profile_data, headers=headers, cookies=cookies, verify=os.getenv("CERTFILE"))
        logger.debug(f'api_signup > createProfile > Response: {response}')
        logger.debug(f'api_signup > createProfile > Response status code: {response.status_code}')
        
        response.raise_for_status()
        if response.status_code == 201:
            logger.debug('api_signup > createProfile > Profile created in profile service')
            return True
        else:
            logger.error(f'api_signup > createProfile > Unexpected status code: {response.status_code}')
            return False
    except requests.RequestException as e:
        logger.error(f'api_signup > createProfile > Failed to create profile: {e}')
        return False


def api_signup(request):
    logger.debug("api_signup")
    language = request.headers.get('X-Language', 'en')
    activate(language)
    if request.method == 'POST':
        try:
          data = json.loads(request.body)
          # logger.debug(f'Received data: {data}')
          form = SignUpForm(data=data)
          if form.is_valid():
                user = form.save(commit=False)

                # Password validation
                password = data.get('password') # clear text password
                
                user.password = make_password(data['password']) # hashed password
                user = form.save()
                username = data.get('username')
                logger.info(f'api_signup > User.username: {user.username}, hased pwd {user.password}')

                user_obj = User.objects.get(username=username)

                # Check if the user is active
                if not user_obj.is_active:
                    logger.debug('api_signup > User is inactive')
                    user.delete()
                    return JsonResponse({
                        'status': 'error', 
                        'message': _('User is inactive')
                    }, status=400)
                
                csrf_token = request.COOKIES.get('csrftoken')
                # Create a profile through call to profileapi service
                if not createProfile(username, user.id, csrf_token, False, language):
                        user.delete()
                        return JsonResponse({
                            'status': 'error', 
                            'message': _('Failed to create profile')
                        }, status=500)

                # Ensure the password meets the minimum requirements
                validate_password(password)
                # if validate_password(password) == None:
                #   raise DjangoValidationError(['Not a valid password'])

                jwt_token, refresh_jwt_token = generate_jwt_token(user)
        
                # Create response object
                response = JsonResponse({
                    'status': 'success',
                    'type': 'login_successful',
                    'message': _('Login successful'),
                    'token': jwt_token,
                    'user_id': user.id
                })

                # Set the JWT token in the headers and a secure cookie
                response['Authorization'] = f'Bearer {jwt_token}'
                response.set_cookie(
                    key='jwt_token',
                    value=jwt_token,
                    httponly=True,
                    secure=True,
                    samesite='Lax',
                    max_age=60 * 60 * 24 * 7,
                )
                response.set_cookie(
                    key='refresh_jwt_token',
                    value=refresh_jwt_token,
                    httponly=True,
                    secure=True,
                    samesite='Lax',
                    max_age=60 * 60 * 24 * 7,
                )       
                return response
              
          else:
              logger.debug('api_signup > Invalid form')
              errors = json.loads(form.errors.as_json())
              logger.debug(f'Errors: {errors}')
              # message = errors.get('username')[0].get('message')
              message = None
              if errors:
                message = next((error['message'] for field_errors in errors.values() for error in field_errors), None)
              logger.debug(f'message: {message}')
              return JsonResponse({'status': 'error', 'message': message}, status=400)
        except json.JSONDecodeError:
            logger.debug('api_signup > Invalid JSON')
            return JsonResponse({'status': 'error', 'message': _('Invalid JSON')}, status=400)
        except DjangoValidationError as e:
                  logger.debug(f'Password validation error: {e.messages}')
                  return JsonResponse({'status': 'error', 'message': _('Not a valid password')}, status=400)
        except Exception as e:
            logger.error(f'api_signup > Unexpected error: {e}')
            return JsonResponse({'status': 'error','message': _('An unexpected error occurred')}, status=500)
    logger.debug('api_signup > Method not allowed')
    return JsonResponse({'status': 'error', 'message': _('Method not allowed')}, status=405)

def api_check_username_exists(request):
    logger.debug("api_check_exists")
    language = request.headers.get('X-Language', 'en')
    activate(language)
    if request.method == 'POST':
        try:
          data = json.loads(request.body)
          username = data.get('username')
          if User.objects.filter(username=username).exists():
              logger.debug('api_check_exists > User exists')
              return JsonResponse({'status': 'success', 'message': _('User exists')})
          else:
              logger.debug('api_check_exists > User does not exist')
              return JsonResponse({'status': 'failure', 'message': _('User does not exist')}, status=404)
        except json.JSONDecodeError:
            logger.debug('api_check_exists > Invalid JSON')
            return JsonResponse({'status': 'error', 'message': _('Invalid JSON')}, status=400)
    logger.debug('api_check_exists > Method not allowed')
    return JsonResponse({'status': 'error', 'message': _('Method not allowed')}, status=405)


def api_edit_profile(request):
  logger.debug("api_edit_profile")
  language = request.headers.get('X-Language', 'en')
  activate(language)
  if request.method == 'POST':
    try:
      data = json.loads(request.body)
      logger.debug(f'data: {data}')

      # Check the user id changed is the same as the user id in the token

      user_id = data.get('user_id')
      user_obj = User.objects.get(id=user_id)
      #user_obj = User.objects.filter(id=user_id).first()
      logger.debug(f'user_obj username: {user_obj.username}, user_obj id: {user_obj.id}')

      # Password validation
      new_password = data.get('new_password')
      validate_password(new_password)
      
      if request.user.id_42 and request.headers.get('sudo') != "add" :
        return JsonResponse({'status': 'error', 'message': _('Unauthorized')}, status=401)
    
      form = EditProfileForm(data, instance=user_obj)
      # logger.debug(f'form: {form}')
      
      if form.is_valid():
        logger.debug('api_edit_profile > Form is valid')
        form.save()
        return JsonResponse({
              'status': 'success',
              'type': 'profile_updated',
              'message': _('Profile updated'),
              'status': 200
            })
      else:
        logger.debug('api_edit_profile > Form is invalid')
        return JsonResponse({'status': 'error', 'message': _('Invalid profile update')}, status=400)
    except json.JSONDecodeError:
      logger.debug('api_edit_profile > Invalid JSON')
      return JsonResponse({'status': 'error', 'message': _('Invalid JSON')}, status=400)    
    except User.DoesNotExist:
      logger.debug('api_edit_profile > User not found')
      return JsonResponse({'status': 'error', 'message': _('User not found')}, status=404)
    except DjangoValidationError as e:
          logger.debug(f'Password validation error: {e.messages}')
          return JsonResponse({'status': 'error', 'message': _('Not a valid password')}, status=400)
  else:
    logger.debug('api_edit_profile > Method not allowed')
    return JsonResponse({'status': 'error', 'message': _('Method not allowed')}, status=405)


def exchange_code_for_token(auth_code):
    data = {
        'grant_type': 'authorization_code',
        'client_id': settings.CLIENT_ID,
        'client_secret': settings.CLIENT_SECRET,
        'code': auth_code,
        'redirect_uri': settings.REDIRECT_URI,
    }
    response = requests.post('https://api.intra.42.fr/oauth/token', data=data)
    return response.json()

def get_42_user_data(token):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get('https://api.intra.42.fr/v2/me', headers=headers)
    return response.json()


# def create_or_get_user(request, user_data):
#     """
#     Creates a new user or retrieves an existing one based on the 42 API data.
#     Logs in the user after creation or retrieval, and calls the profile API to create the profile.
#     """
#     language = request.headers.get('X-Language', 'en')
#     activate(language)
#     try:
#         # Try to find the user by their 42 login (username)
#         user = User.objects.get(username=user_data['login'])
#         logger.info(f"User found: {user.username}")
#     except User.DoesNotExist:
#         # Check if this is a "42 user" by seeing if `id` exists in user_data (or any other identifier for 42 user)
#         if 'id' in user_data:  # Assuming `id` from user_data corresponds to 42 ID
#             data = {"username": user_data['login'], "id_42": user_data['id']}  # No password needed for 42 users

#             # Bypass the password field if user is 42-based
#             form = SignUpForm(data=data)
#             if form.is_valid():
#                 user = form.save()
#             else:
#                 logger.error(f"SignUpForm error: {form.errors}")
#         else:
#             # Create a standard user with a password if not a 42 user
#             data = {"username": user_data['login'], "password": "1", "confirm_password": "1"}
#             form = SignUpForm(data=data)
#             if form.is_valid():
#                 user = form.save()
#             else:
#                 logger.error(f"SignUpForm error: {form.errors}")
        
#         # Create the profile
#         createProfile(user_data['login'], user_data['id'], "", 'id' in user_data, language)  # True if 42 user
#         payload = json.dumps({'image_url': user_data['image']['link']})  # Convert the data to a JSON string
#         csrf_token = request.COOKIES.get('csrftoken')  # Get CSRF token from cookies
#         jwt_token = request.COOKIES.get('jwt_token')

#         headers = {
#             'X-CSRFToken': csrf_token,
#             'Cookie': f'csrftoken={csrf_token}',
#             'Content-Type': 'application/json',
#             'Referer': 'https://authentif:9001',
#             'Authorization': f'Bearer {jwt_token}',
#         }
        
#         # Make the POST request to the external authentif service
#         response = requests.post("https://gateway:8443/download_42_avatar/", data=payload, headers=headers, verify=os.getenv("CERTFILE"))
#         csrf_token = request.COOKIES.get('csrftoken')  # Get CSRF token from cookies
#         jwt_token = request.COOKIES.get('jwt_token')

#         headers = {
#             'X-CSRFToken': csrf_token,
#             'Cookie': f'csrftoken={csrf_token}',
#             'Content-Type': f"{response.json()['avatar']['content_type']}",
#             'Referer': 'https://authentif:9001',
#             'Authorization': f'Bearer {jwt_token}',
#         }

#         response = requests.post("https://gateway:8443/post_edit_profile_avatar", body=response.text, headers=headers, verify=os.getenv("CERTFILE"))
        
        

        
#     if user == None:
#         login(request, user)

#     return user


@csrf_exempt
def oauth(request):
    language = request.headers.get('X-Language', 'en')
    activate(language)
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    # Get the 'code' parameter from the parsed JSON data
    auth_code = data.get('code')
    state = data.get('state')
    
    if not auth_code:
        return JsonResponse({'error': 'Authorization code is missing'}, status=400)

    # Step 2: Exchange authorization code for access token
    try:
        token_data = exchange_code_for_token(auth_code)
    except Exception as e:
        logger.error(f"Error exchanging authorization code: {str(e)}")
        return JsonResponse({'error': 'Failed to retrieve access token'}, status=500)

    if 'access_token' not in token_data:
        return JsonResponse({'error': 'Failed to retrieve access token'}, status=400)

    # Step 3: Retrieve user data from 42 API
    try:
        user_data = get_42_user_data(token_data['access_token'])
    except Exception as e:
        logger.error(f"Error fetching user data: {str(e)}")
        return JsonResponse({'error': 'Failed to retrieve user data'}, status=500)

    # Step 4: Create or authenticate the user and generate a JWT
    try:
        # Try to find the user by their 42 login (username)
        user = User.objects.get(username=user_data['login'])
        logger.info(f"User found: {user.username}")
        jwt_token, refresh_jwt_token = generate_jwt_token(user)  # Ensure this function is properly implemented
        response = JsonResponse({
          'status': 'success',
          'type': 'login_successful',
          'message': _('Login successful'),
          'token': jwt_token,
          'user_id': user.id
        })
        response['Authorization'] = f'Bearer {jwt_token}'
        response.set_cookie(
        key='jwt_token',
        value=jwt_token,
        httponly=True,  # Prevent JavaScript access to the cookie (for security)
        secure=True,  # Only send the cookie over HTTPS (ensure your environment supports this)
        samesite='Lax',  # Control cross-site request behavior
        max_age=60 * 60 * 24 * 7,  # Cookie expiration (optional, e.g., 7 days)
        )
        response.set_cookie(
        key='refresh_jwt_token',
        value=refresh_jwt_token,
        httponly=True,  # Prevent JavaScript access to the cookie (for security)
        secure=True,  # Only send the cookie over HTTPS (ensure your environment supports this)
        samesite='Lax',  # Control cross-site request behavior
        max_age=60 * 60 * 24 * 7,  # Cookie expiration (optional, e.g., 7 days)
        )
        return response
    except User.DoesNotExist:
        # Check if this is a "42 user" by seeing if `id` exists in user_data (or any other identifier for 42 user)
        if 'id' in user_data:  # Assuming `id` from user_data corresponds to 42 ID
            data = {"username": user_data['login'], "id_42": user_data['id']}  # No password needed for 42 users

            # Bypass the password field if user is 42-based
            form = SignUpForm(data=data)
            if form.is_valid():
                user = form.save()
            else:
                logger.error(f"SignUpForm error: {form.errors}")

    csrf_token = request.COOKIES.get('csrftoken')  # Get CSRF token from cookies

    # Create the profile
    createProfile(user_data['login'], user.id, csrf_token, 'id' in user_data, language)  # True if 42 user
    if user == None:
        login(request, user)

    jwt_token, refresh_jwt_token = generate_jwt_token(user)  # Ensure this function is properly implemented

    payload = json.dumps({'image_url': user_data['image']['link']})  # Convert the data to a JSON string
    logger.debug(f"payload: {payload}")
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Cookie': f'csrftoken={csrf_token}',
        'Content-Type': 'application/json',
        'Referer': 'https://authentif:9001',
        'Authorization': f'Bearer {jwt_token}',
    }

    # Make the POST request to the external authentif service
    response = requests.post("https://gateway:8443/download_42_avatar/",cookies=request.COOKIES,data=payload,headers=headers,verify=os.getenv("CERTFILE"))

    # If the response is a file (an image), we need to handle it differently.
    if response.status_code == 200:
        # Get the content type from the response
        content_type = response.headers['Content-Type']
        image_name = response.headers.get('Content-Disposition').split('filename=')[1].strip('\"')

        # Prepare the multipart form data for editing the profile avatar
        files = {
            'avatar': (image_name, response.content, content_type)  # Sending the image as a file
        }

        csrf_token = request.COOKIES.get('csrftoken')  # Get CSRF token from cookies

        headers = {
            'X-CSRFToken': csrf_token,
            'Authorization': f'Bearer {jwt_token}',
            'Referer': 'https://authentif:9001',
        }
        cookies = {
        'csrftoken': f'{csrf_token}',
        'jwt_token': f'{jwt_token}',
        'sudo': 'add',
        }

        # Send the image to edit_profile_avatar
        edit_response = requests.post(
            "https://gateway:8443/edit_profile_avatar/",
            cookies=cookies,
            files=files,  # Sending the files parameter for multipart
            headers=headers,
            verify=os.getenv("CERTFILE")
        )

        if edit_response.status_code == 200:
            print("Avatar updated successfully.")
        else:
            print(f"Failed to update avatar: {edit_response.content}")

    else:
        print(f"Failed to download avatar: {response.content}")

    headers = {
            'X-CSRFToken': csrf_token,
            'Cookie': f'csrftoken={csrf_token}',
            'Content-Type': 'application/json',
            'Referer': 'https://authentif:9001',
            'Authorization': f'Bearer {jwt_token}',
    }
    
    if user_data['languages_users'][0]['language_id'] == 11:
        language = 'es'
    elif user_data['languages_users'][0]['language_id'] == 1:
        language = 'fr'
    else:
        language = 'en'

    payload = json.dumps({
        "csrfmiddlewaretoken": f"{csrf_token}",
        "username": f"{user_data['login']}",
        "display_name": f"{user_data['login']}",
        "country": f"{user_data['campus'][0]['country']}",
        "city": f"{user_data['campus'][0]['city']}",
        "preferred_language": f"{language}"
    })

    cookies = {
        'csrftoken': f'{csrf_token}',
        'jwt_token': f'{jwt_token}',
        'sudo': 'add',
    }

    response = requests.post("https://gateway:8443/edit_profile_general/",cookies=cookies,data=payload,headers=headers,verify=os.getenv("CERTFILE"))
    # Create response object
    response = JsonResponse({
        'status': 'success',
        'type': 'login_successful',
        'message': _('Login successful'),
        'token': jwt_token,
        'user_id': user.id
    })

    # Set the JWT token in the headers
    response['Authorization'] = f'Bearer {jwt_token}'

    # Set the JWT token in a cookie (with security options)
    response.set_cookie(
        key='jwt_token',
        value=jwt_token,
        httponly=True,  # Prevent JavaScript access to the cookie (for security)
        secure=True,  # Only send the cookie over HTTPS (ensure your environment supports this)
        samesite='Lax',  # Control cross-site request behavior
        max_age=60 * 15,
    )
    response.set_cookie(
        key='refresh_jwt_token',
        value=refresh_jwt_token,
        httponly=True,  # Prevent JavaScript access to the cookie (for security)
        secure=True,  # Only send the cookie over HTTPS (ensure your environment supports this)
        samesite='Lax',  # Control cross-site request behavior
        max_age=60 * 60 * 24 * 7,
    )
    response.set_cookie('django_language', language, httponly=False, secure=True, samesite='Lax')
    
    return response


@login_required
def enable2FA(request):
    language = request.headers.get('X-Language', 'en')
    activate(language)
    logger.debug("enable2FA")
    logger.debug(f"request.method: {request.method}")

    if request.method != 'POST':
        return JsonResponse({"status": 'error', 'message': _('Invalid request method. Use POST.')}, status=405)
    
    if request.user.id_42:
        return JsonResponse({"status": 'error', 'message': _('Unauthorized')}, status=401)
    
    if request.user.id is None or request.user.id == 0:
        return JsonResponse({"status": 'error', 'message': _('Unauthorized'), 'qr_code': "", 'two_fa_enabled': False}, status=401)
    
    user = User.objects.get(pk=request.user.id)

    if user.two_factor_token:
        # 2FA is already enabled for the user
        return JsonResponse({'status': 'error', 'message': _('2FA is already enabled'), 'qr_code': "", 'two_fa_enabled': True}, status=200)

    # Generate a new TOTP secret and QR code
    totp = pyotp.TOTP(pyotp.random_base32())
    secret = totp.secret

    # Store the secret temporarily in the cache with a short expiration time
    cache_key = f"2fa_setup_{user.id}"
    cache.set(cache_key, secret, timeout=300)  # Cache for 5 minutes

    # Generate QR code for authenticator app
    qr = qrcode.make(totp.provisioning_uri(name=str(user.username), issuer_name="Pongscendence"))
    qr_io = BytesIO()
    qr.save(qr_io, format="PNG")
    qr_io.seek(0)

    # Encode QR code in base64
    qr_code_base64 = base64.b64encode(qr_io.getvalue()).decode('utf-8')
    qr_code_url = f"data:image/png;base64,{qr_code_base64}"
    
    return JsonResponse({
        'status': 'success',
        'message': _('Scan the QR code, then enter the OTP below to confirm'),
        'qr_code': qr_code_url,
        'two_fa_enabled': False
    }, status=200)

@login_required
def confirmEnable2FA(request):
    language = request.headers.get('X-Language', 'en')
    activate(language)
    # Check if the request is a POST request
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": _("Invalid request method. Use POST.")}, status=405)

    if request.user.id_42:
        return JsonResponse({"status": "error", "message": _("Unauthorized")}, status=401)


    if request.user.id is None or request.user.id == 0:
        return JsonResponse({"status": "error", "message": _("Unauthorized")}, status=401)

    # Get OTP code from request body
    try:
        body = json.loads(request.body)
        otp_code = body.get("otp_code")
        if not otp_code:
            return JsonResponse({"status": "error", "message": _("OTP code is required")}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": _("Invalid JSON format")}, status=400)

    # Retrieve temporary TOTP secret from cache
    cache_key = f"2fa_setup_{request.user.id}"
    temp_secret = cache.get(cache_key)
    if not temp_secret:
        return JsonResponse({"status": "error", "message": _("No 2FA setup in progress or setup expired")}, status=400)

    # Verify OTP using the TOTP secret
    totp = pyotp.TOTP(temp_secret)
    if totp.verify(otp_code):
        # OTP is correct, enable 2FA by saving the token to the user's profile
        user = request.user
        user.two_factor_token = temp_secret
        user.save()

        # Remove the temporary token from cache
        cache.delete(cache_key)

        return JsonResponse({
            "status": "success",
            "message": _("2FA is now enabled"),
            "two_fa_enabled": True
        }, status=200)
    else:
        return JsonResponse({"status": "error", "message": _("Invalid OTP code")}, status=400)

@login_required
def disable2FA(request):
    language = request.headers.get('X-Language', 'en')
    activate(language)
    if request.method == 'POST':
        if request.user.id_42:
            return JsonResponse({"status": "error", "message": _("Unauthorized")}, status=401)

        user = User.objects.get(pk=request.user.id)
        if user.two_factor_token:
            user.two_factor_token = None
            user.save()
            return JsonResponse({"status": "success", "message": _("2FA disabled successfully")})
        else:
            return JsonResponse({"status": "error", "message": _("2FA is not enabled")}, status=400)
    return JsonResponse({"status": "error", "message": _("Invalid request")}, status=400)


def verify2FA(request, user_id):
    language = request.headers.get('X-Language', 'en')
    activate(language)
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": _("Invalid request method. Use POST.")}, status=405)

    # Ensure user_id is provided
    if not user_id:
        return JsonResponse({"status": "error", "message": _("User ID is required")}, status=400)

    # Attempt to retrieve the user and check if they have 2FA enabled
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": _("User not found")}, status=404)

    if not user.two_factor_token:
        return JsonResponse({"status": "error", "message": _("2FA is not enabled for this user")}, status=400)

    # Retrieve and verify the OTP code
    payload = json.loads(request.body)  # Decode the JSON request body
    otp_code = payload.get('otp_code')  # Extract the otp_code

    if not otp_code:
        return JsonResponse({"status": "error", "message": _("OTP code is required")}, status=400)

    # Use pyotp to verify the provided OTP code
    totp = pyotp.TOTP(user.two_factor_token)
    if totp.verify(otp_code):
        new_token, refresh_jwt_token = generate_jwt_token(user)

        # Respond with success and set the new JWT as a secure cookie
        response = JsonResponse({"status": "success", 'type': 'login_successful', "message": _("Login successful"), "token": new_token})
        response.set_cookie('jwt_token', new_token, httponly=True, secure=True, samesite='Lax')
        response.set_cookie('refresh_jwt_token', refresh_jwt_token, httponly=True, secure=True, samesite='Lax')

        return response
    else:
        return JsonResponse({"status": "error", "message": _("Invalid OTP code")}, status=400)