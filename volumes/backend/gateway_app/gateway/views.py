import os, json, requests, logging
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.translation import activate, gettext as _
from .consumerMainRoom import users_connected
from .authmiddleware import login_required
logger = logging.getLogger(__name__)

def get_home(request):
    if request.user.is_authenticated:
        logger.info(f"IN GET HOME > USERNAME: {request.user.username}")
    status = request.GET.get('status', '')
    message = request.GET.get('message', '')
    type_msg = request.GET.get('type', '')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        context = {'user': request.user}

        if type_msg == 'header':
            html = render_to_string('includes/header.html', context=context, request=request)
        elif type_msg == 'chat':
            html = render_to_string('includes/chat_modal.html', context=context, request=request)
        else:
            html = render_to_string('fragments/home_fragment.html', context=context, request=request)
        
        response = JsonResponse({'html': html, 'status': status, 'message': message, 'user_id': request.user.id}, status=200)

        if not request.COOKIES.get('django_language'):
            response.set_cookie('django_language', 'en', httponly=False, secure=True, samesite='Lax')
        return response

    response = render(request, 'partials/home.html', {'status': status, 'message': message})

    if not request.COOKIES.get('django_language'):
        response.set_cookie('django_language', 'en', httponly=False, secure=True, samesite='Lax')
        
    return response


@login_required
def get_friends(request):
  if request.method != 'GET':
    return redirect('405')

  # Get friends
  profile_api_url = 'https://profileapi:9002/api/getfriends/' + str(request.user.id) + '/'
  response = requests.get(profile_api_url, verify=os.getenv("CERTFILE"))
  friends = response.json()
  if response.status_code == 200:
    # Add 'online': true to friends who are in users_connected
    for friend in friends:
      if friend['user_id'] in users_connected:
        friend['online'] = True
    return JsonResponse({'friends': friends}, status=200)


@login_required
def list_friends(request):
    if request.method != 'GET':
      return redirect('405')

    # Get friends
    profile_api_url = 'https://profileapi:9002/api/getfriends/' + str(request.user.id) + '/'
    response = requests.get(profile_api_url, verify=os.getenv("CERTFILE"))
    friends = response.json()

    request_user_profile = requests.get('https://profileapi:9002/api/profile/' + str(request.user.id) + '/', verify=os.getenv("CERTFILE"))
    response_user_profile = request_user_profile.json()

    if response.status_code == 200 and request_user_profile.status_code == 200:

      # Add 'online': true to friends who are in users_connected
      for friend in friends:
        if not friend['im_blocked'] and friend['user_id'] in users_connected:
          friend['online'] = True

      blocked_users = response_user_profile['blocked_users']
      
      if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # if friends is empty
        if not friends or len(friends) == 0:
          html = render_to_string('fragments/myfriends_fragment.html', request=request)
          return JsonResponse({'html': html, 'status': 200})
        else:
          html = render_to_string('fragments/myfriends_fragment.html', {'friends': friends}, request=request)
          return JsonResponse({'html': html, 'status': 200})
      return render(request, 'partials/myfriends.html', {'friends': friends})
    
    else:
      if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Error retrieving friends'}, status=500)
      return render(request, 'partials/myfriends.html', {'error': _('Error retrieving friends')})

def set_language(request):
    if request.method != 'POST':
        return redirect('405')
    
    try:
      data = json.loads(request.body)
    except json.JSONDecodeError:
      return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    
    language = data.get('language')
    activate(language)
    response = JsonResponse({'language': language}, status=200)
    response.set_cookie('django_language', language, httponly=False, secure=True, samesite='Lax')
    return response


def get_translations(request):
  if request.method != 'GET':
    return redirect('405')
  
  token = request.headers.get('X-Custom-Token')
  if token != 'mega-super-duper-secret-token':
    return redirect('home')

  translations = {
    'notificationMsg': _("Notification"),
    'friendRequestReceived': _(" sent you a friend request."),
    'friendRequestAccepted': _(" accepted your friend request."),
    'friendRequestDeclined': _(" declined your friend request."),
    'gameRequestReceived': _(" has invited you to play: "),
    'gameRequestAccepted': _(" has accepted your game request."),
    'gameRequestDeclined': _(" has declined your game request."),
    'gameRequestCancelled': _(" has cancelled the game request."),
    'gameWaitingToPlay': _(" is waiting to play."),
    'gamePlayNextTournament': _(" you play next in the tournament."),
    'gameRequestUnconnected': _("  is not connected. Game invite cancelled."),
    'userBlocked': _(" has blocked you."),
    'userUnblocked': _(" has unblocked you."),
    'afterBlockMsg': _("Friend blocked successfully."),
    'afterUnblockMsg': _("Friend unblocked successfully."),
    'formSubmissionError': _("Form submission error. Please reload and retry."),
    'noFriendsmsg': _("No friends yet"),
    'selectFriendmsg': _("Select a contact"),
    'profileUpdatedmsg': _("Profile updated"),
  }

  return JsonResponse(translations, status=200)
