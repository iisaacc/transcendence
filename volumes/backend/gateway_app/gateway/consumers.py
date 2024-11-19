import json, asyncio, logging, requests, os
from channels.generic.websocket import AsyncWebsocketConsumer
from .handleInvite import get_authentif_variables, find_matching_usernames, is_valid_key
logger = logging.getLogger(__name__)

class FormConsumer(AsyncWebsocketConsumer):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.usernames = []

  async def connect(self):
    # Accept the WebSocket connection
      await self.accept()
      # Send an initial message to confirm the connection
      await self.send(text_data=json.dumps({
        'type': 'connection_established',
        'message': 'You are connected!'
      }))
      self.user_input = ""

  async def disconnect(self, close_code):
      pass
    
  async def receive(self, text_data):
      # Handle messages received from the client

      # Parse the JSON message
      key_pressed = json.loads(text_data).get('key', '')
      user_id = json.loads(text_data).get('userID', '')
      if user_id:
        self.user_id = user_id
        profile_data = get_authentif_variables(self.user_id)
        self.usernames = sorted(profile_data.get('usernames', []))

      # update key pressed
      if key_pressed == 'Backspace':
          self.user_input = self.user_input[:-1]
      elif key_pressed.isascii() and is_valid_key(key_pressed):
          self.user_input += key_pressed
      
      # If the user input is empty, send back an empty list
      if not self.user_input:
        await self.send(text_data=json.dumps({
          'type': 'suggestions',
          'suggestions': [],
          'message': 'Suggestions sent!'
        }))
        return

      # Find matching usernames
      matching_usernames = find_matching_usernames(self.usernames, self.user_input)

      # Send back suggestions based on the constructed string
      await self.send(text_data=json.dumps({
        'type': 'suggestions',
        'suggestions': matching_usernames,
        'message': 'Suggestions sent!'
      }))

  


