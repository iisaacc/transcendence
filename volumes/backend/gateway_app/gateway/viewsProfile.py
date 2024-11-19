import os, json, logging, requests, mimetypes, asyncio, aiohttp
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from .forms import InviteFriendFormFrontend, EditProfileFormFrontend, LogInFormFrontend
from django.utils.translation import gettext as _
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .utils import getUserProfile, getDjangoLanguageCookie

import prettyprinter
from prettyprinter import pformat
prettyprinter.set_default_config(depth=None, width=80, ribbon_width=80)

User = get_user_model()
logger = logging.getLogger(__name__)

def get_profileapi_variables(request=None, response=None):
  if response is not None:
    user_id = int(response.json().get('user_id'))
  else:
    user_id = request.user.id
  profile_api_url = 'https://profileapi:9002/api/profile/' + str(user_id) + '/'
  response = requests.get(profile_api_url, verify=os.getenv("CERTFILE"))
  if response.status_code == 200:
    return response.json()
  else:
    status = response.status_code
    message = response.json().get('message')
    return {'status': 'error', 'message': message, 'status_code': status
            }

@login_required
def get_profile(request):
    if request.method != 'GET':
      return redirect('405')
    form = InviteFriendFormFrontend()

    # GET profile user's variables
    profile_data = get_profileapi_variables(request=request)
    if profile_data.get('status') == 'error':
        return redirect(profile_data.get('status_code'))

    # Ensure the user has a profile
    if profile_data.get('status') == 'error':
        return redirect('404')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('fragments/profile_fragment.html', {'form': form, 'profile_data': profile_data}, request=request)
        return JsonResponse({'html': html, 'status': 'success'})
    return render(request, 'partials/profile.html', {'form': form, 'profile_data': profile_data})

@login_required
def get_edit_profile(request):
    if request.method != 'GET':
        return redirect('405')

    # GET profile user's variables
    profile_data = get_profileapi_variables(request=request)
    if profile_data.get('status') == 'error':
        return redirect(profile_data.get('status_code'))
    profile_data['username'] = request.user.username

    form = EditProfileFormFrontend()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('fragments/edit_profile_fragment.html', {'form': form, 'profile_data': profile_data, 'user': request.user}, request=request)
        return JsonResponse({'html': html})
    return render(request, 'partials/edit_profile.html', {'form': form, 'profile_data': profile_data, 'user': request.user})

@login_required
def get_friend_profile(request, friend_id):
    if request.method != 'GET':
        return redirect('405')
    
    form = InviteFriendFormFrontend()
    
    # Get friend's profile
    profile_api_url = f'https://profileapi:9002/api/getFullProfile/{friend_id}/'
    response = requests.get(profile_api_url, verify=os.getenv("CERTFILE"))
    if response.status_code != 200:
        return JsonResponse({'status': 'error', 'message': 'Error retrieving friend profile'})
    
    profile_data = response.json()
    
    # Get user's profile
    user_profile_api_url = f'https://profileapi:9002/api/getFullProfile/{request.user.id}/'
    user_response = requests.get(user_profile_api_url, verify=os.getenv("CERTFILE"))
    if user_response.status_code != 200:
        return JsonResponse({'status': 'error', 'message': 'Error retrieving user profile'})
    
    user_profile_data = user_response.json()
    
    # Check if the user is blocked
    is_blocked = friend_id in user_profile_data.get('blocked_users', [])
    im_blocked = request.user.id in profile_data.get('blocked_users', [])

    # Pass the information to the template
    context = {
        'form': form,
        'profile_data': profile_data,
        'is_blocked': is_blocked,
        'im_blocked': im_blocked,
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('fragments/friend_profile_fragment.html', context, request=request)
        return JsonResponse({'html': html, 'status': 'success', 'is_blocked': is_blocked, 'im_blocked': im_blocked})
    return render(request, 'partials/friend_profile.html', context)

@login_required
def get_match_history(request, username):
    if request.method != 'GET':
        return redirect('405')
    try:
       user_id = User.objects.get(username=username).id
    except:
        return JsonResponse({'status': 'error', 'message': 'Error retrieving match history of a non-existing user'})
    get_history_url = 'https://play:9003/api/getGames/' + str(user_id) + '/'
    response = requests.get(get_history_url, verify=os.getenv("CERTFILE"))
    if response.status_code == 200:
        games_data = response.json().get('games_data')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
          html = render_to_string('fragments/match_history_fragment.html', {'games_data': games_data, 'user_id': user_id, 'username': username}, request=request)
          return JsonResponse({'html': html, 'status': 'success'})
        return render(request, 'partials/match_history.html', {'games_data': games_data, 'user_id': user_id, 'username': username})
    else:
        return JsonResponse({'status': 'error', 'message': 'Error retrieving match history'})
    
@login_required
def view_user_profile(request, user_id):
    if request.method != 'GET':
        return redirect('405')
    
    try:
        user = User.objects.get(id=user_id)
        profile = getUserProfile(user_id)
        
    except:
        return redirect('404')
    
    get_history_url = 'https://play:9003/api/userGames/' + str(user_id) + '/'
    response = requests.get(get_history_url, verify=os.getenv("CERTFILE"))

    if response.ok:
        data = response.json().get('data')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('fragments/userprofile_fragment.html',
                                    {
                                       'data': data,
                                       'target': {
                                          'user_id': user_id,
                                          'username': user.username,
                                          'avatar': user.avatar,
                                          'profile': profile
                                        }
                                    }, request=request)
            return JsonResponse({'html': html, 'status': 'success'})
        
        return render(request, 'partials/userprofile.html', {
                                       'data': data,
                                       'target': {
                                          'user_id': user_id,
                                          'username': user.username,
                                          'avatar': user.avatar,
                                          'profile': profile
                                        }
                                    })
    else:
        return JsonResponse({'status': 'error', 'message': _('Error retrieving match history')})

@login_required
def post_edit_profile_security(request):
    if request.method != 'POST':
        return redirect('405')

    # Cookies & headers
    csrf_token = request.COOKIES.get('csrftoken')
    django_language = getDjangoLanguageCookie(request)
    jwt_token = request.COOKIES.get('jwt_token')
    headers = {
        'X-CSRFToken': csrf_token,
        'X-Language': django_language,
        'Cookie': f'csrftoken={csrf_token}',
        'Content-Type': 'application/json',
        'Referer': 'https://gateway:8443',
        'Authorization': f'Bearer {jwt_token}',
    }

    # Recover data from the form
    data = json.loads(request.body)
    data['user_id'] = request.user.id

    profile_data = get_profileapi_variables(request=request)
    if profile_data.get('status') == 'error':
        return redirect(profile_data.get('status_code'))

    # Check form is valid
    form = EditProfileFormFrontend(data)
    if not form.is_valid():
        message = _("Invalid form data")
        form.add_error(None, message)
        html = render_to_string('fragments/edit_profile_fragment.html', {'form': form, 'profile_data': profile_data, 'user': request.user}, request=request)
        return JsonResponse({'html': html, 'status': 'error', 'message': message}, status=400)
    elif security_data_is_valid(data) == False:
        form.add_error(None, data['message'])
        html = render_to_string('fragments/edit_profile_fragment.html', {'form': form, 'profile_data': profile_data, 'user': request.user}, request=request)
        return JsonResponse({'html': html, 'status': 'error', 'message': data['message']}, status=400)

    # Send and recover response from the profileapi service
    authentif_url = 'https://authentif:9001/api/editprofile/' 
    response = requests.post(authentif_url, json=data, headers=headers, verify=os.getenv("CERTFILE"))
    status = response.json().get("status")
    message = response.json().get("message")
    type = response.json().get("type")
    
     # Redirection usage
    form = LogInFormFrontend()
    preferred_language = profile_data.get('preferred_language')

    if response.ok:
      user_response =  JsonResponse({'type': type, 'status': status, 'message': message})
      user_response.set_cookie('django_language', preferred_language, httponly=False, secure=True, samesite='Lax')
      return user_response

    #handle wrong confirmation password
    else:
      if profile_data.get('status') == 'error':
        return redirect(profile_data.get('status_code'))
      data = json.loads(request.body)
      form = EditProfileFormFrontend(data)
      form.add_error(None, message)

      html = render_to_string('fragments/edit_profile_fragment.html', {'form': form, 'profile_data': profile_data, 'user': request.user}, request=request)
      return JsonResponse({'html': html, 'status': status, 'message': message}, status=response.status_code)


def general_data_is_valid(data):
  display_name = data.get('display_name')
  city = data.get('city')
  country = data.get('country')

  # Check if the fields are empty
  if (display_name is None or display_name == ""):
    data['message'] = _("Display name cannot be empty")
    return False
  if (city is None or city == "" or city.isspace()):
    data['message'] = _("City cannot be empty")
    return False
  if (country is None or country == "" or country.isspace()):
    data['message'] = _("Country cannot be empty")
    return False
  # Check if display_name has spaces
  if ' ' in display_name:
    data['message'] = _("Display name cannot contain spaces")
    return False
  return True

def security_data_is_valid(data):
  username = data.get('username')
  if (username is None or username == ""):
    data['message'] = _("Username cannot be empty")
    return False
  if ' ' in username:
    data['message'] = _("Username cannot contain spaces")
    return False
  return True


@login_required
def post_edit_profile_general(request):
    if request.method != 'POST':
        return redirect('405')

    # Cookies & headers
    csrf_token = request.COOKIES.get('csrftoken')
    django_language = getDjangoLanguageCookie(request)
    jwt_token = request.COOKIES.get('jwt_token')
    headers = {
        'X-CSRFToken': csrf_token,
        'X-Language': django_language,
        'Cookie': f'csrftoken={csrf_token}',
        'Content-Type': 'application/json',
        'Referer': 'https://gateway:8443',
        'Authorization': f'Bearer {jwt_token}',
    }

    # Recover data from the form
    data = json.loads(request.body)
    data['user_id'] = request.user.id

    profile_data = get_profileapi_variables(request=request)
    if profile_data.get('status') == 'error':
        return redirect(profile_data.get('status_code'))

    # Check form is valid
    form = EditProfileFormFrontend(data)
    if not form.is_valid():
        message = _("Invalid form data")
        form.add_error(None, message)
        html = render_to_string('fragments/edit_profile_fragment.html', {'form': form, 'profile_data': profile_data, 'user': request.user}, request=request)
        return JsonResponse({'html': html, 'status': 'error', 'message': message}, status=400)
    elif general_data_is_valid(data) == False:
        form.add_error(None, data['message'])
        html = render_to_string('fragments/edit_profile_fragment.html', {'form': form, 'profile_data': profile_data, 'user': request.user}, request=request)
        return JsonResponse({'html': html, 'status': 'error', 'message': data['message']}, status=400)

    # Send and recover response from the profileapi service
    profileapi_url = 'https://profileapi:9002/api/editprofile/' 
    response = requests.post(profileapi_url, json=data, headers=headers, verify=os.getenv("CERTFILE"))
    status = response.json().get("status")
    message = response.json().get("message")
    type = response.json().get("type")

    # Redirection usage
    form = EditProfileFormFrontend()
    if profile_data.get('status') == 'error':
        return redirect(profile_data.get('status_code'))

    if response.ok:
        preferred_language = data.get('preferred_language')
        user_response =  JsonResponse({'status': status, 'type': type, 'message': message, 'preferred_language': preferred_language})
        user_response.set_cookie('django_language', preferred_language, httponly=False, secure=True, samesite='Lax')

        return user_response
        
    #handle displayName already taken
    else:
      if profile_data.get('status') == 'error':
        return redirect(profile_data.get('status_code'))
      data = json.loads(request.body)
      form = EditProfileFormFrontend(data)
      form.add_error(None, message)
      html = render_to_string('fragments/edit_profile_fragment.html', {'form': form, 'profile_data': profile_data, 'user': request.user}, request=request)
      return JsonResponse({'html': html, 'status': status, 'message': message}, status=response.status_code)

@login_required
def post_edit_profile_avatar(request):
  if request.method != 'POST':
      return redirect('405')

  # Cookies & headers
  csrf_token = request.COOKIES.get('csrftoken')
  django_language = getDjangoLanguageCookie(request)
  jwt_token = request.COOKIES.get('jwt_token')
  sudo_token = request.COOKIES.get('sudo')
  headers = {
        'X-CSRFToken': csrf_token,
        'X-Language': django_language,
        'Cookie': f'csrftoken={csrf_token}',
        'Content-Type': 'application/json',
        'Referer': 'https://gateway:8443',
        'Authorization': f'Bearer {jwt_token}',
        'sudo': f'{sudo_token}',
    }

  # Redirection usage
  form = EditProfileFormFrontend()
  profile_data = get_profileapi_variables(request=request)
  if profile_data.get('status') == 'error':
    return redirect(profile_data.get('status_code'))
  preferred_language = profile_data.get('preferred_language')

  # Recover data from the form
  data = request.POST.copy()

  # Check if the avatar file is empty
  if request.FILES.get('avatar') is not None:
      
    # Get the uploaded file   
    uploaded_file = request.FILES['avatar']

    # Check if the file is an image
    if not uploaded_file.content_type.startswith('image'):
        form = EditProfileFormFrontend(data)
        form.add_error(None, _('Please select an image file'))
        html = render_to_string('fragments/edit_profile_fragment.html', {'form': form, 'profile_data': profile_data, 'user': request.user}, request=request)
        return JsonResponse({'html': html, 'status': 'error'}, status=400)

    # Save the uploaded file
    avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
    fs = FileSystemStorage(location=avatar_dir)
    filename = fs.save(uploaded_file.name, uploaded_file)

    # Construct the data to send to the profileapi service
    data['user_id'] = request.user.id
    data['username'] = request.user.username
    data['avatar'] = '/avatars/' + filename
    authentif_url = 'https://authentif:9001/api/editprofile/' 
    response = requests.post(authentif_url, json=data, headers=headers, verify=os.getenv("CERTFILE"))
    status = response.json().get("status")
    message = response.json().get("message")
    type = response.json().get("type")
    html = render_to_string('fragments/edit_profile_fragment.html', {'form': form, 'profile_data': profile_data, 'user': request.user}, request=request)

    if  response.ok:
        user_response =  JsonResponse({'type': type, 'message': message, 'status': 'success'})
        user_response.set_cookie('django_language', preferred_language, httponly=False, secure=True, samesite='Lax')
        return user_response
    else:
      html = render_to_string('fragments/edit_profile_fragment.html', {'status': status, 'message': message, 'form': form, 'profile_data': profile_data, 'user': request.user}, request=request)
      return JsonResponse({'html': html, 'status': status, 'message': message})
  
  # Handle the case where no file is uploaded
  else:
    form = EditProfileFormFrontend(data)
    form.add_error(None, _('Please select an image file'))
    html = render_to_string('fragments/edit_profile_fragment.html', {'form': form, 'profile_data': profile_data, 'user': request.user}, request=request)
    return JsonResponse({'html': html, 'status': 'error'}, status=400)


@login_required
def download_42_avatar(request):
    if request.method == 'POST':
      
        # Get the image URL from the POST data
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)            

        # Get the image URL from the parsed JSON
        image_url = body_data.get('image_url')
        
        if not image_url:
            return JsonResponse({'error': 'No image URL provided'}, status=400)

        try:
            # Download the image
            response = requests.get(image_url)
            response.raise_for_status()

            # Get the image content
            image_content = response.content

            # Extract the image name from the URL
            image_name = image_url.split("/")[-1]

            # Determine the MIME type of the file
            mime_type, _ = mimetypes.guess_type(image_name)

            # Create a response object with the image content
            multipart_response = HttpResponse(image_content, content_type=mime_type)
            multipart_response['Content-Disposition'] = f'attachment; filename={image_name}'

            return multipart_response

        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

async def checkNameExists(request):
    if request.method != 'POST':
      return redirect('405')
    data = json.loads(request.body)

    if request.user.id != 0:
        user_profile = get_profileapi_variables(request)
        if user_profile.get('status') == 'error':
            return redirect(profile_data.get('status_code'))
        if data['name'] == user_profile['display_name'] or data['name'] == request.user.username:
            return JsonResponse({'status': 'success', 'message': 'display name and username are available'})

    csrf_token = request.COOKIES.get('csrftoken')
    django_language = getDjangoLanguageCookie(request)
    jwt_token = request.COOKIES.get('jwt_token')
    headers = {
        'X-CSRFToken': csrf_token,
        'X-Language': django_language,
        'Cookie': f'csrftoken={csrf_token}',
        'Content-Type': 'application/json',
        'Referer': 'https://gateway:8443',
        'Authorization': f'Bearer {jwt_token}',
    }

    # Check if the display name already exists
    profile_api_url = 'https://profileapi:9002/api/checkDisplaynameExists/'
    response = requests.post(profile_api_url, json=data, headers=headers, verify=os.getenv("CERTFILE"))

    status = response.json().get("status")
    message = response.json().get("message")

    if response.ok:
        # if display name doesn't exists, check username
        if status == 'failure': 
          # Check if the username already exists
          authentif_url = 'https://authentif:9001/api/checkUsernameExists/'
          response = requests.post(authentif_url, json=data, headers=headers, verify=os.getenv("CERTFILE"))

          status = response.json().get("status")
          message = response.json().get("message")

          if response.ok:
              # if display name doesn't exists, check username
              if status == 'failure': 
                return JsonResponse({'status': 'success', 'message': 'display name and username are available'})
              else:
                return JsonResponse({'status': 'failure', 'message': 'Name not available'}) 
        else:
          return JsonResponse({'status': 'failure', 'message': 'Name not available'})    
    
    return JsonResponse({'status': 'error', 'message': message})
