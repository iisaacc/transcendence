import logging, random
logger = logging.getLogger(__name__)


def update_player_hit_state(gs, frameCount):
    if gs['player1_hit'] and frameCount == gs['player1_frame_hit'] + 10:
        gs['player1_hit'] = False

    elif gs['player2_hit'] and frameCount == gs['player2_frame_hit'] + 10:
        gs['player2_hit'] = False


def spawn_cows(gs, cfg, frameCount):
  if frameCount % 30 == 0 \
    or (frameCount % 20 == 0 and frameCount >= 200) \
    or (frameCount % 10 == 0 and frameCount >= 300) \
    or (frameCount % 5 == 0 and frameCount >= 400) \
    or (frameCount % 2 == 0 and frameCount >= 800):

      gs['cows'].append({
          "x": cfg['canvas']['width'] / 2 - random.uniform(-15, 45),
          "y": cfg['canvas']['height'] / 2 - random.uniform(-15, 45),
          "vx": random.uniform(-8, 8),
          "vy": random.uniform(-8, 8),
        });


def update_cows_pos(gs, cfg):
  for cow in gs['cows']:
      cow['x'] += cow['vx']
      cow['y'] += cow['vy']
      
      if cow['x'] < -cfg['cowDimension'] or cow['y'] < -cfg['cowDimension'] or cow['x'] > cfg['canvas']['width'] or cow['y'] > cfg['canvas']['height']:
          gs['cows'].remove(cow)


def check_collisions(gs, cfg, frameCount):
  for cow in gs['cows']:
      player1Hit = False
      player2Hit = False

      # Check if cow hit a player
      if (cow['x'] < gs['player1X'] + cfg['playerDimension'] and
          cow['x'] + cfg['cowDimension'] > gs['player1X'] and
          cow['y'] < gs['player1Y'] + cfg['playerDimension'] and
          cow['y'] + cfg['cowDimension'] > gs['player1Y']):
          player1Hit = True

      if (cow['x'] < gs['player2X'] + cfg['playerDimension'] and
          cow['x'] + cfg['cowDimension'] > gs['player2X'] and
          cow['y'] < gs['player2Y'] + cfg['playerDimension'] and
          cow['y'] + cfg['cowDimension'] > gs['player2Y']):
          player2Hit = True

      # if the cow hit both players, randomly keep one to be hit
      if player1Hit == True and player2Hit == True:
            if random.choice([True, False]):
              player1Hit = False
            else:
              player2Hit = False

      if player1Hit == True:
          gs['cows'].remove(cow)
          gs['scorePlayer1'] = gs['scorePlayer1'] - 1 if gs['scorePlayer1'] > 0 else 0
          gs['player1_frame_hit'] = frameCount
          gs['player1_hit'] = True
          logger.debug("CowsCalcLocal > check_collisions > cow hit player 1")
      elif player2Hit == True:
          gs['cows'].remove(cow)
          gs['scorePlayer2'] = gs['scorePlayer2'] - 1 if gs['scorePlayer2'] > 0 else 0
          gs['player2_frame_hit'] = frameCount
          gs['player2_hit'] = True
          logger.debug("CowsCalcLocal > check_collisions > cow hit player 2")
      
      # Break loop if a player has 0
      if gs['scorePlayer1'] == 0 or gs['scorePlayer2'] == 0:
        break
