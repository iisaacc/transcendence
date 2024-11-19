from django.http import JsonResponse, HttpResponse
from profileapi.forms import InviteFriendForm
from profileapi.models import Profile, Notification
from profileapi.forms import EditProfileForm
from django.db import DatabaseError
from django.utils.translation import activate, gettext as _
import json
import os
import requests
import logging
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

def getDisplayNameUnused(data):
    logger.debug("setDisplayNameUnused")
    profiles = Profile.objects.all()
    index = 1
    for profile in profiles:
        if profile.display_name == data['username']:
            displayname = data['username'] + str(index)
            while Profile.objects.filter(display_name=displayname).exists():
                index += 1
                displayname = displayname + str(index)
            return displayname
    return data['username']

@csrf_exempt
def api_signup(request):
    logger.debug("--> hello from api_signup")
    language = request.headers.get('X-Language', 'en')
    activate(language)
    if (request.method != 'POST'):
        logger.debug("Method not allowed")
        return HttpResponse('Method not allowed', status=405)
    logger.debug("--> POST method")
    data = json.loads(request.body)
    display_name = getDisplayNameUnused(data)
    logger.debug(f"data : {data}")
    try:
      profile = Profile(
        user_id=data['user_id'],
        display_name= display_name,
      )
      logger.debug("--> profile user_id created")
      profile.save()
      logger.debug("--> profile created")
      return JsonResponse({
            'status': 'success',
            'type': 'signup_successful',
            'message': _('Signup successful')
          }, status=201)
    except Exception as e:
      return JsonResponse({'error': str(e)}, status=400)

def api_edit_profile(request):
    logger.debug("")
    logger.debug("api_edit_profile")
    # language = request.headers.get('X-Language', 'en')
    # activate(language)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.debug(f'api_edit_profile > data: {data}')
            user_id = data.get('user_id')
            logger.debug(f'api_edit_profile > user_id: {user_id}')

            # Use get_object_or_404 to handle the case where the user is not found
            user_obj = Profile.objects.get(user_id=user_id)
            logger.debug('api_edit_profile > current user_obj recovered')

            # Log the current profile data
            logger.debug(f'Current profile, country: {user_obj.country}, city: {user_obj.city}, preferred_language: {user_obj.preferred_language}')
            logger.debug('------------------------------')

            # Ensure data is passed as a dictionary
            form = EditProfileForm(data, instance=user_obj)
            logger.debug(f'api_edit_profile > form: {form}')

            language = data.get('preferred_language')
            activate(language)

            if form.is_valid():
                logger.debug('api_edit_profile > Form is valid')
                form.save()
                return JsonResponse({
                      'status': 'success',
                      'type': 'profile_updated',
                      'message': _('Profile updated')
                    }, status=200)
            else:
                logger.debug('api_edit_profile > Form is invalid')
                return JsonResponse({'status': 'error', 'message': _('Invalid profile data')}, status=400)
        except (json.JSONDecodeError, DatabaseError) as e:
            logger.debug(f'api_edit_profile > Invalid JSON error: {str(e)}')
            return JsonResponse({'status': 'error', 'message': _('Error: ') + str(e)}, status=400)
    else:
        logger.debug('api_edit_profile > Method not allowed')
        return JsonResponse({'status': 'error', 'message': _('Method not allowed')}, status=405)

def get_full_profile(request, user_id):
    logger.debug("get_full_profile")
    id = int(user_id)
    logger.debug(f"id: {id}")
    authentif_url = 'https://authentif:9001/api/getUserInfo/' + str(id) + '/'
    try:
        authentif_response = requests.get(authentif_url, verify=os.getenv("CERTFILE"))
        authentif_data = authentif_response.json()
        user_obj = Profile.objects.get(user_id=id)
        logger.debug('user_obj recovered')
        data = {
              'user_id': user_obj.user_id,
              'username': authentif_data['username'],
              'avatar': '/media/' + authentif_data['avatar_url'],
              'country': user_obj.country,
              'city': user_obj.city,
              'display_name': user_obj.display_name,
              'preferred_language': user_obj.preferred_language,
              'blocked_users': list(user_obj.blocked_users.values_list('id', flat=True)),
            }
        return JsonResponse(data, status=200)
    except Profile.DoesNotExist:
        logger.debug('get_profile > User not found')
        return JsonResponse({'status': 'error', 'message': _('User not found')}, status=404)
    except Exception as e:
        logger.debug(f'get_profile > {str(e)}')
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def get_friends(request, user_id):
    logger.debug("get_friends")
    id = int(user_id)
    logger.debug(f"id: {id}")
    try:
        user_obj = Profile.objects.get(user_id=id)
        logger.debug('user_obj recovered')
        friends = user_obj.friends.all()
        logger.debug('friends recovered')
        data = []
        for friend in friends:
            # Recover username and avatar from authentif app
            authentif_url = 'https://authentif:9001/api/getUserInfo/' + str(friend.user_id) + '/'
            response = requests.get(authentif_url, verify=os.getenv("CERTFILE"))
            user_data = response.json()
            logger.debug(f'get_friends > user_data: {user_data}')
            if friend in user_obj.blocked_users.all():
                is_blocked = True
            else:
                is_blocked = False
            if user_obj in friend.blocked_users.all():
                im_blocked = True
            else:
                im_blocked = False
            data.append({
                'user_id': friend.user_id,
                'display_name': friend.display_name,
                'country': friend.country,
                'city': friend.city,
                'preferred_language': friend.preferred_language,
                'avatar': '/media/' + user_data['avatar_url'],
                'username': user_data['username'],
                'is_blocked': is_blocked,
                'im_blocked': im_blocked,
            })
        return JsonResponse(data, status=200, safe=False)
    except Profile.DoesNotExist:
        logger.debug('get_friends > User not found')
        return JsonResponse({'status': 'error', 'message': _('User not found')}, status=404)
    except Exception as e:
        logger.debug(f'get_friends > {str(e)}')
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def get_profile_api(request, user_id):
    logger.debug("")
    logger.debug("get_profile_api")
    id = int(user_id)
    logger.debug(f"id: {id}")
    try:
        user_obj = Profile.objects.get(user_id=id)
        logger.debug('user_obj recovered')
        data = {
              'user_id': user_obj.user_id,
              'country': user_obj.country,
              'city': user_obj.city,
              'display_name': user_obj.display_name,
              'preferred_language': user_obj.preferred_language,
              'blocked_users': list(user_obj.blocked_users.values_list('id', flat=True)),
              'status': 'success',
            }
        return JsonResponse(data, status=200)
    except Profile.DoesNotExist:
        logger.debug('get_profile > User not found')
        return JsonResponse({'status': 'error', 'message': _('User not found')}, status=404)
    except Exception as e:
        logger.debug(f'get_profile > {str(e)}')
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def get_users_ids(request):
    logger.debug("get_users_ids")
    try:
        users = Profile.objects.all()
        logger.debug('users recovered')
        data = []
        for user in users:
            data.append(user.user_id)
        return JsonResponse(data, status=200, safe=False)
    except Exception as e:
        logger.debug(f'get_users_ids > {str(e)}')
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def get_blocked_users(request, sender_id, receiver_id):
  logger.debug("get_blocked_users")
  try:
    sender_obj = Profile.objects.get(user_id=sender_id)
    receiver_obj = Profile.objects.get(user_id=receiver_id)
    logger.debug('sender_obj and receiver_obj recovered')

    sender_blocked_users = sender_obj.blocked_users.all()
    receiver_blocked_users = receiver_obj.blocked_users.all()
    logger.debug(f'blocked_users recovered: {sender_blocked_users}')
    logger.debug(f'blocked_users recovered: {receiver_blocked_users}')

    # Assuming sender_blocked_users is a queryset of blocked users
    if sender_blocked_users.filter(user_id=receiver_id).exists():
      return JsonResponse({'status': 'success', 'message': _('User is blocked')}, status=200)
    elif receiver_blocked_users.filter(user_id=sender_id).exists():
      return JsonResponse({'status': 'blocked', 'message': _('User is blocked')}, status=200)
    else:
      logger.debug('get_blocked_users > User is not blocked')
      return JsonResponse({'status': 'blocked', 'message': _('User is not blocked')}, status=200)

  except Profile.DoesNotExist:
    logger.debug('get_blocked_users > User not found')
    return JsonResponse({'status': 'unblocked', 'message': _('User not found')}, status=404)

# If an unresponded friend request or game request already exists , we delete the previous notification (call this function after a friend/game request has been accepted)

# If an unresponded friend/game request already exists from the same sender to the same receiver, we delete the previous notification (call this function before creating a same request)
def check_if_double_request_exists(request, sender_id, receiver_id, type):
  logger.debug('')
  logger.debug('check_if_double_request_exists')
  notifications = Notification.objects.filter(type=type)
  for notification in notifications:
    if int(notification.sender.user_id) == int(sender_id) and int(notification.receiver.user_id) == int(receiver_id) and (notification.status == 'read' or notification.status == 'unread'):
      logger.debug('check_if_double_request_exists > request already exists')
      logger.debug('delete double invitation')
      return JsonResponse({'status': 'error', 'message': _('You have already sent an unresponded request to this user')})
  logger.debug('check_if_double_request_exists > request does not exist')
  return JsonResponse({'status': 'success', 'message': _('Request does not exist')})


def create_notifications(request):
    logger.debug("create_notifications")

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.debug(f'data: {data}')
            sender_id = data.get('sender_id')
            receiver_id = data.get('receiver_id')
            message = data.get('message')
            type = data.get('type')
            game_type = data.get('game_type', None)
            if (sender_id == receiver_id):
                return JsonResponse({'status': 'error', 'message': _('You cannot send a notification to yourself')}, status=400)


            sender_obj = Profile.objects.get(user_id=sender_id)
            receiver_obj = Profile.objects.get(user_id=receiver_id)
            logger.debug('sender_obj and receiver_obj recovered')
            notification = Notification(
                sender=sender_obj,
                receiver=receiver_obj,
                message=message,
                type=type,
                game_type=game_type,
            )
            notification.save()

            return JsonResponse({'status': 'success', 'message': _('Notification created')}, status=201)
        except (json.JSONDecodeError, DatabaseError) as e:
            logger.debug(f'create_notifications > Invalid JSON error: {str(e)}')
            return JsonResponse({'status': 'error', 'message': 'Error: ' + str(e)}, status=400)
    else:
        logger.debug('create_notifications > Method not allowed')
        return JsonResponse({'status': 'error', 'message': _('Method not allowed')}, status=405)

def check_if_users_are_blocked(sender_id, receiver_id):
  logger.debug("check_if_users_are_blocked")
  try:
    sender_obj = Profile.objects.get(user_id=sender_id)
    receiver_obj = Profile.objects.get(user_id=receiver_id)
    logger.debug('sender_obj and receiver_obj recovered')
    if receiver_obj in sender_obj.blocked_users.all():
      logger.debug('check_if_users_are_blocked > User is blocked')
      return True
    elif sender_obj in receiver_obj.blocked_users.all():
      logger.debug('check_if_users_are_blocked > User is blocked')
      return True
    else:
      logger.debug('check_if_users_are_blocked > User is not blocked')
      return False
  except Profile.DoesNotExist:
    logger.debug('check_if_users_are_blocked > User not found')
    return JsonResponse({'status': 'error', 'message': _('User not found')}, status=404)


def get_notifications(request, user_id):
    logger.debug("get_notifications")
    id = int(user_id)
    logger.debug(f"id: {id}")
    try:
        user_obj = Profile.objects.get(user_id=id)
        logger.debug('user_obj recovered')
        notifications = Notification.objects.filter(receiver=user_obj)
        data = []
        for notification in notifications:
            # If users are blocked, we do not send the notification
            if check_if_users_are_blocked(notification.sender.user_id, notification.receiver.user_id) == False:
                data.append({
                    'sender': notification.sender.user_id,
                    'receiver': notification.receiver.user_id,
                    'message': notification.message,
                    'type': notification.type,
                    'date': notification.date,
                    'status': notification.status,
                    'game_type': notification.game_type,
                })
                logger.debug(f'notification data: {data}')
            else:
               logger.debug('get_notifications > User is blocked')
        return JsonResponse(data, status=200, safe=False)
    except Profile.DoesNotExist:
        logger.debug('get_notifications > User not found')
        return JsonResponse({'status': 'error', 'message': _('User not found')}, status=404)
    except Exception as e:
        logger.debug(f'get_notifications exception > {str(e)}')
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

# def accept_friend_request(request, sender_id, receiver_id, sender_obj, receiver_obj):
#   # Save the friendship in the database
#   sender_obj.friends.add(receiver_obj)
#   sender_obj.save()
#   receiver_obj.save()

#   # Check if their is a symetric friend request
#   check_if_symetric_request_exists(request, sender_id, receiver_id, 'friend_request')



def set_notif_as_readen(request, sender_id, receiver_id, type, response):
    logger.debug("set_notif_as_readen")
    try:
        sender_obj = Profile.objects.get(user_id=sender_id)
        receiver_obj = Profile.objects.get(user_id=receiver_id)
        if (type == 'friend_request_response'):
          request_type = 'friend_request'
        else:
          request_type = 'game_request'


        logger.debug('sender_obj and receiver_obj recovered')
        notifications = Notification.objects.filter(sender=sender_obj, receiver=receiver_obj, type=request_type)
        logger.debug('notifications recovered')
        for notification in notifications:
            if (response == 'accept'):
              notification.status = 'accepted'
            elif (response == 'decline'):
              notification.status = 'declined'
            notification.save()
            logger.debug('notification marked as read')

            # if friend request accepted, save friendship in database
            if response == 'accept' and type == 'friend_request_response':
                sender_obj.friends.add(receiver_obj)
                sender_obj.save()
                receiver_obj.save()
            # if notification accepted, check if their is a symetric request
    except Profile.DoesNotExist:
        logger.debug('set_notif_as_readen > User not found')
        return JsonResponse({'status': 'error', 'message': _('User not found')}, status=404)
    return JsonResponse({'status': 'success', 'message': _('Notification marked as read')}, status=200)


def set_all_notifs_as_readen(request, receiver_id):
    logger.debug("set_all_notifs_as_readen")
    try:
        receiver_obj = Profile.objects.get(user_id=receiver_id)
        logger.debug('receiver_obj recovered')
        notifications = Notification.objects.filter(receiver=receiver_obj, status='unread')
        logger.debug('notifications recovered')
        for notification in notifications:
            notification.status = 'read'
            notification.save()
            logger.debug('notification marked as read')
    except Profile.DoesNotExist:
        logger.debug('set_all_notifs_as_readen > User not found')
        return JsonResponse({'status': 'error', 'message': _('User not found')}, status=404)
    return JsonResponse({'status': 'success', 'message': _('All notifications marked as read')}, status=200)

def check_friendship(request, sender_id, receiver_id):
    logger.debug("check_friendship")
    try:
        sender_obj = Profile.objects.get(user_id=sender_id)
        receiver_obj = Profile.objects.get(user_id=receiver_id)
        logger.debug('sender_obj and receiver_obj recovered')
        if receiver_obj in sender_obj.friends.all():
            logger.debug('check_friendship > Friendship exists')
            return JsonResponse({'status': 'success', 'message': _('Friendship exists')}, status=200)
        else:
            logger.debug('check_friendship > Friendship does not exist')
            return JsonResponse({'status': 'failure', 'message': _('Friendship does not exist')}, status=200)
    except Profile.DoesNotExist:
        logger.debug('check_friendship > User not found')
        return JsonResponse({'status': 'error', 'message': _('User not found')}, status=404)

def check_displayname_exists(request):
    logger.debug("check_displayname_exists")
    if request.method == 'POST':
        try:
          data = json.loads(request.body)
          name_to_test = data.get('name')
          if Profile.objects.filter(display_name=name_to_test).exists():
              logger.debug('check_displayname_exists > User exists')
              return JsonResponse({'status': 'success', 'message': _('User exists')})
          else:
              logger.debug('check_displayname_exists > User does not exist')
              return JsonResponse({'status': 'failure', 'message': _('User does not exist')}, status=404)
        except json.JSONDecodeError:
            logger.debug('check_displayname_exists > Invalid JSON')
            return JsonResponse({'status': 'error', 'message': _('Invalid JSON')}, status=400)
    logger.debug('check_displayname_exists > Method not allowed')
    return JsonResponse({'status': 'error', 'message': _('Method not allowed')}, status=405)

def block_friends(request, friend_id):
    logger.debug("block_friends")
    language = request.headers.get('X-Language', 'en')
    activate(language)
    try:
        if request.method != 'POST':
            logger.debug('block_friends > Method not allowed')
            return JsonResponse({'status': 'error', 'message': _('Method not allowed')}, status=405)
        data = json.loads(request.body)
        user_id = data.get('user_id')
        logger.debug('request.user.id: ' + str(user_id))
        user_obj = Profile.objects.get(user_id=user_id)
        logger.debug('user_obj recovered')
        friend_obj = Profile.objects.get(user_id=friend_id)
        logger.debug('friend_obj recovered')
        user_obj.blocked_users.add(friend_obj)
        user_obj.save()
        logger.debug('Friend blocked')
        return JsonResponse({'status': 'success', 'message': _('Friend blocked')}, status=200)
    except Profile.DoesNotExist:
        logger.debug('block_friends > User not found')
        return JsonResponse({'status': 'error', 'message': _('User not found')}, status=404)

def unblock_friends(request, friend_id):
    logger.debug("unblock_friends")
    language = request.headers.get('X-Language', 'en')
    activate(language)
    try:
        if request.method != 'POST':
            logger.debug('unblock_friends > Method not allowed')
            return JsonResponse({'status': 'error', 'message': _('Method not allowed')}, status=405)
        data = json.loads(request.body)
        user_id = data.get('user_id')
        logger.debug('request.user.id: ' + str(user_id))
        user_obj = Profile.objects.get(user_id=user_id)
        logger.debug('user_obj recovered')
        friend_obj = Profile.objects.get(user_id=friend_id)
        logger.debug('friend_obj recovered')
        user_obj.blocked_users.remove(friend_obj)
        user_obj.save()
        logger.debug('Friend unblocked')
        return JsonResponse({'status': 'success', 'message': _('Friend unblocked')}, status=200)
    except Profile.DoesNotExist:
        logger.debug('unblock_friends > User not found')
        return JsonResponse({'status': 'error', 'message': _('User not found')}, status=404)
    except Exception as e:
        logger.debug(f'unblock_friends > {str(e)}')
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)