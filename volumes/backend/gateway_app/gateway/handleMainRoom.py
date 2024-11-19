import json, asyncio, logging, requests, os
from datetime import datetime
from .handleInvite import get_authentif_variables
from django.utils.translation import activate, gettext as _
from django.template.loader import render_to_string
import prettyprinter
from prettyprinter import pformat
prettyprinter.set_default_config(depth=None, width=80, ribbon_width=80)


logger = logging.getLogger(__name__)

def readMessage(message):
  return message

async def requestResponse(content, users_connected, receiver_avatar_url, self):
  sender_id = content.get('sender_id', '')
  sender_username = content.get('sender_username', '')
  receiver_username = content.get('receiver_username', '')
  receiver_id = content.get('receiver_id', '')
  sender_avatar_url = content.get('sender_avatar_url', '')
  game_mode = content.get('game_mode', '')
  game_type = content.get('game_type', '')
  html = ''
  receiver_avatar_url = receiver_avatar_url
  
  response = content.get('response', '')
  type = content.get('type', '')

  if type == 'friend_request_response' and response == 'accept':
    message = _('has accepted your friend request.')
  elif type == 'friend_request_response' and response == 'decline':
    message = _('has declined your friend request.')
  elif type == 'game_request_response' and response == 'accept':
    message = _('is waiting to play ') + game_type.capitalize()
  elif type == 'game_request_response' and response == 'decline':
    message = _('has declined the game request.')
  elif type == 'cancel_waiting_room':
    message = _('has canceled the game request.')
    user = { 'username': receiver_username }
    context = {
        'user': user,
        'session': self.scope['session'],
        'cookies': self.scope['cookies'],
    }
    html = render_to_string('fragments/home_fragment.html', context=context)
  elif type == 'next_in_tournament':
    message = content.get('notify_player', '')
    receiver_id = sender_id
    receiver_username = sender_username

  # Send response to frontend sender
  if sender_id in users_connected:
    for connection in users_connected[sender_id]:
      await connection.send_json({
        'type': type,
        'response': response,
        'message': message,
        'sender_username': sender_username,
        'sender_id': sender_id,
        'sender_avatar_url': sender_avatar_url,
        'receiver_username': receiver_username,
        'receiver_avatar_url': receiver_avatar_url,
        'receiver_id': receiver_id,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'game_mode': game_mode,
        'game_type': game_type,
        'html': html,
      })
  
  
  # Set the notification as read
  profileapi_url = 'https://profileapi:9002/api/setnotifasread/' + str(sender_id) + '/' + str(receiver_id) + '/' + str(type) + '/' + str(response) + '/'
  csrf_token = self.scope['cookies']['csrftoken']
  headers = {
          'X-CSRFToken': csrf_token,
          'Cookie': f'csrftoken={csrf_token}',
          'Content-Type': 'application/json',
          'HTTP_HOST': 'profileapi',
          'Referer': 'https://gateway:8443',
      }
  
  try:
    response = requests.get(profileapi_url, headers=headers, verify=os.getenv("CERTFILE"))

  except Exception as e:
    logger.error(f'requestResponse > Error marking notification as read: {e}')
    return

   # Save the notification in database
  message = receiver_username + ' ' + message
  profileapi_url = 'https://profileapi:9002/api/createnotif/'
  notification_data = { 'sender_id': receiver_id, 'receiver_id': sender_id, 'message': message, 'type': type, 'game_type': game_type }
  try:
    response = requests.post(
          profileapi_url, json=notification_data, headers=headers, verify=os.getenv("CERTFILE"))

    response.raise_for_status()
    if response.status_code == 201:
      logger.debug(f'requestResponse > Notification saved in database')
    else:
      logger.error(f'requestResponse > Error saving notification')
  except Exception as e:
    logger.error(f'requestResponse > Error saving notification: {e}')

async def friendRequest(content, users_connected, self):
  sender_id = content.get('sender_id', '')
  sender_username = content.get('sender_username', '')
  receiver_id = content.get('receiver_id', '')
  sender_avatar_url = content.get('sender_avatar_url', '')
  msg_body = _('sent you a friend request')
  message = sender_username + ' ' + msg_body
  game_type = content.get('game_type', '')
  receiver_avatar_url = content.get('receiver_avatar_url', '')

  # Get username of receiver
  user_data = get_authentif_variables(receiver_id)
  receiver_username = user_data.get('username', '')
  if user_data is None:
    return

  # Save friend request in database
  profileapi_url = 'https://profileapi:9002/api/createnotif/'
  notification_data = { 'sender_id': sender_id, 'receiver_id': receiver_id, 'message': message, 'type': 'friend_request', 'game_type': game_type }
  csrf_token = self.scope['cookies']['csrftoken']
  headers = {
      'X-CSRFToken': csrf_token,
      'Cookie': f'csrftoken={csrf_token}',
      'Content-Type': 'application/json',
      'HTTP_HOST': 'profileapi',
      'Referer': 'https://gateway:8443',
  }
  try:
    response = requests.post(
          profileapi_url, json=notification_data, headers=headers, verify=os.getenv("CERTFILE"))

    response.raise_for_status()
    if response.status_code == 201:
      # Check if user_id is in users_connected
      if receiver_id in users_connected:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for connection in users_connected[receiver_id]:
          await connection.send_json({
            'type': 'friend_request',
            'message': message,
            'sender_username': sender_username,
            'sender_id': sender_id,
            'sender_avatar_url': sender_avatar_url,
            'receiver_avatar_url': self.avatar_url,
            'receiver_username': receiver_username,
            'receiver_id': receiver_id,
            'date': date,
            'receiver_avatar_url': receiver_avatar_url
          })
    else:
      logger.error(f'friendRequest > Error saving friend request in database')
  except Exception as e:
    logger.error(f'friendRequest > Error saving friend request in database: {e}')
    return

async def handleNewConnection(self, users_connected):
  # Get user id from URL
  self.user_id = self.scope['url_route']['kwargs']['user_id']
  # If user is not connected, close connection
  if (self.user_id == 'None' or self.user_id == 0):
    await self.close()
    return

# Check if user is already connected
  if self.user_id not in users_connected:
    users_connected[self.user_id] = []
  users_connected[self.user_id].append(self)
  await self.send_json({
      'message': 'You are connected to the main room!',
      'type': 'user_connected',
  })

  # Get user info
  user_data = get_authentif_variables(self.user_id)
  if user_data is not None:
    self.username = user_data.get('username', '')
    self.avatar_url = '/media/' + user_data.get('avatar_url', '')
  else:
    await self.close()
    return

  # Broadcast message to room group
  for user, connections in users_connected.items():
    for connection in connections:
        await connection.send_json({
          'message': f'{self.user_id} has joined the main room.',
          'type': 'user_connected',
          'user_id': self.user_id,
        })

async def checkForNotifications(self):
  # Get the database notifications
  profileapi_url = 'https://profileapi:9002/api/getnotif/' + str(self.user_id) + '/'
  csrf_token = self.scope['cookies']['csrftoken']
  headers = {
      'X-CSRFToken': csrf_token,
      'Cookie': f'csrftoken={csrf_token}',
      'Content-Type': 'application/json',
      'HTTP_HOST': 'profileapi',
      'Referer': 'https://gateway:8443',
  }
  response = requests.get(profileapi_url, headers=headers, verify=os.getenv("CERTFILE"))

  response.raise_for_status()
  if response.status_code == 200:
    notifications = sorted(response.json(), key=lambda x: x['date'])
    
    for notification in notifications:

      # Find notification concerning the user_id that are unread
      if notification['receiver'] == self.user_id:

        # Get sender info
        sender_data = get_authentif_variables(notification['sender'])
        sender_username = sender_data.get('username', '')
        sender_avatar_url = '/media/' + sender_data.get('avatar_url', '')

        # Get receiver info
        receiver_data = get_authentif_variables(notification['receiver'])
        receiver_username = receiver_data.get('username', '')
        receiver_avatar_url = '/media/' + receiver_data.get('avatar_url', '')

        # If notif is a response, reverse sender and receiver info
        if notification['type'] == 'game_request_response' or notification['type'] == 'friend_request_response' or notification['type'] == 'cancel_waiting_room':
          sender_username = receiver_data.get('username', '')
          sender_avatar_url = '/media/' + receiver_data.get('avatar_url', '')
          receiver_username = sender_data.get('username', '')
          receiver_avatar_url = '/media/' + sender_data.get('avatar_url', '')

        # Send notification to frontend
        await self.send_json({
          'type': notification['type'],
          'message': notification['message'],
          'sender_id': notification['sender'],
          'sender_username': sender_username,
          'sender_avatar_url': sender_avatar_url,
          'receiver_id': notification['receiver'],
          'receiver_username': receiver_username,
          'receiver_avatar_url': receiver_avatar_url,
          'status': notification['status'],
          'date': notification['date'],
          'game_type': notification['game_type']
        })
  else:
    logger.error(f'checkForNotifications > Error retrieving notifications from database')
    return

async def markNotificationAsRead(self, content, user_id):
  profileapi_url = 'https://profileapi:9002/api/setallnotifasread/' + str(user_id) + '/'
  csrf_token = self.scope['cookies']['csrftoken']
  headers = {
      'X-CSRFToken': csrf_token,
      'Cookie': f'csrftoken={csrf_token}',
      'Content-Type': 'application/json',
      'HTTP_HOST': 'profileapi',
      'Referer': 'https://gateway:8443',
  }
  response = requests.get(profileapi_url, headers=headers, verify=os.getenv("CERTFILE"))

  response.raise_for_status()
  if response.status_code != 200:
    logger.error(f'markNotificationAsRead > Error marking notification as read')
    return


async def checkIfUsersAreBlocked(self, content):
  sender_id = content.get('sender_id', '')
  receiver_id = content.get('receiver_id', '')
  type = content.get('type', '')
  profileapi_url = 'https://profileapi:9002/api/getBlockedUsers/' + str(sender_id) + '/' + str(receiver_id) + '/'
  csrf_token = self.scope['cookies']['csrftoken']
  headers = {
      'X-CSRFToken': csrf_token,
      'Cookie': f'csrftoken={csrf_token}',
      'Content-Type': 'application/json',
      'HTTP_HOST': 'profileapi',
      'Referer': 'https://gateway:8443',
  }
  response = requests.get(profileapi_url, headers=headers, verify=os.getenv("CERTFILE"))
  if response.ok:
    status = response.json().get('status', '')
    if status == 'blocked':
      return True
  else:
    logger.error(f'checkIfUsersAreBlocked > Error checking if users are blocked')
  return False

async def block_user_responses(self, content, users_connected):
  sender_id = content.get('sender_id', '')
  receiver_id = content.get('receiver_id', '')

  # Get usernames
  sender_data = get_authentif_variables(sender_id)
  sender_avatar_url = '/media/' + sender_data.get('avatar_url', '')
  sender_username = sender_data.get('username', '')
  receiver_data = get_authentif_variables(receiver_id)
  receiver_username = receiver_data.get('username', '')
  receiver_avatar_url = '/media/' + receiver_data.get('avatar_url', '')
  game_type = ""
  type = content.get('type', '')
  # Send to the receiver if connected
  if type == 'unblock':
    message = _(' has unblocked you.')
  elif type == 'block':
    message = _(' has blocked you.')
  if receiver_id in users_connected:
    for connection in users_connected[receiver_id]:
      await connection.send_json({
        'type': type,
        'message': message,
        'sender_username': sender_username,
        'sender_id': sender_id,
        'block_sender': False,
        'receiver_username': receiver_username,
        'receiver_avatar_url': receiver_avatar_url,
        'sender_avatar_url': sender_avatar_url,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      })
  
  # Save the notification in database
  if type == 'block':
    message = sender_username + ' ' + message
  if type == 'unblock':
    message = sender_username + message
  profileapi_url = 'https://profileapi:9002/api/createnotif/'
  csrf_token = self.scope['cookies']['csrftoken']
  headers = {
          'X-CSRFToken': csrf_token,
          'Cookie': f'csrftoken={csrf_token}',
          'Content-Type': 'application/json',
          'HTTP_HOST': 'profileapi',
          'Referer': 'https://gateway:8443',
      }
  notification_data = { 'sender_id': sender_id, 'receiver_id': receiver_id, 'message': message, 'type': type, 'game_type': game_type }
  try:
    response = requests.post(
          profileapi_url, json=notification_data, headers=headers, verify=os.getenv("CERTFILE"))

    response.raise_for_status()
    if response.status_code == 201:
      logger.debug(f'requestResponse > Notification saved in database')
    else:
      logger.error(f'requestResponse > Error saving notification')
  except Exception as e:
    logger.error(f'requestResponse > Error saving notification: {e}')
    return


  
  