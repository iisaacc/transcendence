import json, asyncio, logging
from channels.generic.websocket import AsyncWebsocketConsumer 
from .consumersCalcCowsUtils import spawn_cows, update_cows_pos, check_collisions, update_player_hit_state
logger = logging.getLogger(__name__)

class CowsCalcLocal(AsyncWebsocketConsumer):
  # Game configuration constants
  cfg = {
    "canvas": {
      "width": 700,
      "height": 550,
    },
    "maxScore": 5,
    "playerDimension": 40,
    "cowDimension": 50,
    "playerSpeed": 7,
    "keys": { 'w': False, 's': False, 'a': False, 'd': False, 4: False, 5: False, 6: False, 8: False }
  }
  

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.pressed_keys = set()
    # Game state
    self.gs = {
        "player1X": 200,
        "player1Y": self.cfg['canvas']['height'] / 2,
        "player2X": self.cfg['canvas']['width'] - self.cfg['playerDimension'] - 200,
        "player2Y": self.cfg['canvas']['height'] / 2,
        "scorePlayer1": 5,
        "scorePlayer2": 5,
        "player1_hit": False,
        "player1_frame_hit": 0,
        "player2_hit": False,
        "player2_frame_hit": 0,
        "cows": [],
      }
    
    self.frameCount = 0;

    
  async def connect(self):
    # Accept the WebSocket connection
    await self.accept()
    logger.debug("CowsCalcLocal > Client connected")
    # Send an initial message to confirm the connection
    await self.send(text_data=json.dumps({
      'type': 'connection_established, calcgame says hello',
      'message': 'You are connected!',
      'initial_vars': self.cfg,
    }))

  async def disconnect(self, close_code):
    # Handle WebSocket disconnection
    logger.debug("CowsCalcLocal > Client disconnected")
    pass

  async def receive(self, text_data):
    # Handle messages received from the client
    data = json.loads(text_data)
    logger.debug(f"CowsCalcLocal > received data: {data}")
    
    if data['type'] == 'opening_connection, game details':
       self.p1_name = data['p1_name']
       self.p2_name = data['p2_name']
       logger.debug(f"CowsCalcLocal > opening_connection with players: {self.p1_name}, {self.p2_name}")

    if data['type'] == 'next_game, game details':
       self.p1_name = data['p1_name']
       self.p2_name = data['p2_name']
       logger.debug(f"CowsCalcLocal > opening_connection with players: {self.p1_name}, {self.p2_name}")

    if data['type'] == 'players_ready':
        await self.start_game()

    if data['type'] == 'key_press':
      # logger.debug("CowsCalcLocal > key press event")
      self.update_pressed_keys(data['keys'])

  async def start_game(self):
    # Start the game and send initial game state to the client
    logger.debug("CowsCalcLocal > Game started")
    for i in range(3, 0, -1):
        await self.send(text_data=json.dumps({
          'type': 'game_countdown',
          'message': f'Game starting in {i}...',
          'game_state': self.gs,
          'countdown': i,
        }))
        await asyncio.sleep(0.8)

    logger.debug("CowsCalcLocal > sending first game_update")
    await self.send(text_data=json.dumps({
        'type': 'game_update',
        'game_state': self.gs
      }))

    # Start the game loop as a task
    self.game_task = asyncio.create_task(self.game_loop())

  async def game_end(self):
    logger.debug("CowsCalcLocal > Game ended")
    winner = self.p1_name if self.gs['scorePlayer1'] > self.gs['scorePlayer2'] else self.p2_name

    # End the game
    await self.send(text_data=json.dumps({
      'type': 'game_end',
      'message': f'Game Over: {winner} wins!',
      'game_result': {
          'game_winner_name': winner,
          'p1_score': self.gs['scorePlayer1'],
          'p2_score': self.gs['scorePlayer2'],
        }
    }))

    # Cancel the game loop task
    if hasattr(self, 'game_task'):
      self.game_task.cancel()


  async def game_loop(self):
      logger.debug("CowsCalcLocal > game_loop")
      while True:
          # Wait before continuing the loop (in seconds)
          await asyncio.sleep(0.02)
          self.frameCount += 1

          update_player_hit_state(self.gs, self.frameCount)

          spawn_cows(self.gs, self.cfg, self.frameCount)

          self.update_player_pos()

          update_cows_pos(self.gs, self.cfg)

          check_collisions(self.gs, self.cfg, self.frameCount)
          
          # Break loop and end game if a player reaches the max score
          if self.gs['scorePlayer1'] == 0 or self.gs['scorePlayer2'] == 0:
            logger.debug("CowsCalcLocal > Ending game...")
            break
          
          # Send the updated game state to the client
          await self.send(text_data=json.dumps({
              'type': 'game_update',
              'game_state': self.gs
            }))
          # logger.debug(f"Sent game_update, game_state: {self.gs}")
          
      await self.game_end()

  def update_pressed_keys(self, keys):
      # Update the set of pressed keys
      self.pressed_keys = {key: True for key in keys}

  def update_player_pos(self):
    if 'w' in self.pressed_keys and self.gs['player1Y'] > 0:
        logger.debug("CowsCalcLocal > update_paddle_pos > w pressed")
        self.gs['player1Y'] -= self.cfg['playerSpeed']
    
    if 's' in self.pressed_keys and self.gs['player1Y'] < self.cfg['canvas']['height'] - self.cfg['playerDimension']:
        self.gs['player1Y'] += self.cfg['playerSpeed']

    if '8' in self.pressed_keys and self.gs['player2Y'] > 0:
        self.gs['player2Y'] -= self.cfg['playerSpeed']

    if '5' in self.pressed_keys and self.gs['player2Y'] < self.cfg['canvas']['height'] - self.cfg['playerDimension']:
        self.gs['player2Y'] += self.cfg['playerSpeed']

    if 'a' in self.pressed_keys and self.gs['player1X'] > 0:
        self.gs['player1X'] -= self.cfg['playerSpeed']

    if 'd' in self.pressed_keys and self.gs['player1X'] < self.cfg['canvas']['width'] - self.cfg['playerDimension']:
        self.gs['player1X'] += self.cfg['playerSpeed']

    if '4' in self.pressed_keys and self.gs['player2X'] > 0:
        self.gs['player2X'] -= self.cfg['playerSpeed']

    if '6' in self.pressed_keys and self.gs['player2X'] < self.cfg['canvas']['width'] - self.cfg['playerDimension']:
        self.gs['player2X'] += self.cfg['playerSpeed']
