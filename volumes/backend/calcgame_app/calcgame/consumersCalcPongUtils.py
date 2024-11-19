import logging, random
logger = logging.getLogger(__name__)

def getRandomInt(min, max):
  return int((max - min + 1) * random.random() + min)

def update_ball_pos(gs):
  gs['ballX'] += gs['ballSpeedX']
  gs['ballY'] += gs['ballSpeedY']

def check_ball_border_collision(gs, cfg):
  if gs['ballY'] <= cfg['borderWidth'] \
      or gs['ballY'] >= cfg['canvas']['height'] - cfg['ballSize'] - cfg['borderWidth']:
      logger.debug("PongCalcLocal > Ball hits the top or bottom wall")
      gs['ballSpeedY'] = -gs['ballSpeedY']

def check_ball_paddle_collision(gs, cfg, frameCount, lastContactFrame):
  if ( # Ball collision with left paddle
      (lastContactFrame < frameCount - 10
        and gs['ballX'] <= 3 * cfg['paddleWidth']
        and gs['ballX'] > 2 * cfg['paddleWidth']
        and gs['ballY'] + cfg['ballSize'] >= gs['leftPaddleY']
        and gs['ballY'] <= gs['leftPaddleY'] + cfg['paddleHeight']
        and gs['ballSpeedX'] < 0)
      or # Ball collision with right paddle
      (lastContactFrame < frameCount - 10
        and gs['ballX'] >= cfg['canvas']['width'] - 3 * cfg['paddleWidth'] - cfg['ballSize']
        and gs['ballX'] < cfg['canvas']['width'] - 2 * cfg['paddleWidth'] - cfg['ballSize']
        and gs['ballY'] + cfg['ballSize'] >= gs['rightPaddleY']
        and gs['ballY'] <= gs['rightPaddleY'] + cfg['paddleHeight']
        and gs['ballSpeedX'] > 0)
    ):
    logger.debug("PongCalcLocal > Ball hits paddle")
    lastContactFrame = frameCount
    gs['ballSpeedX'] = -getRandomInt(11, 14) if gs['ballSpeedX'] > 0 else getRandomInt(11, 14)
    gs['ballSpeedY'] = getRandomInt(1, 8) if gs['ballSpeedY'] > 0 else -getRandomInt(1, 8)
  elif (
        # Ball collision with sides of left paddle
        (lastContactFrame < frameCount - 50
         and gs['ballX'] <= 3 * cfg['paddleWidth']
         and gs['ballX'] > 2 * cfg['paddleWidth']
         and gs['ballY'] + cfg['ballSize'] >= gs['leftPaddleY']
         and gs['ballY'] <= gs['leftPaddleY'] + cfg['paddleHeight']
         and gs['ballSpeedX'] < 0)
        or  # Ball collision with sides of right paddle
        (lastContactFrame < frameCount - 50
         and gs['ballX'] >= cfg['canvas']['width'] - 3 * cfg['paddleWidth'] - cfg['ballSize']
         and gs['ballX'] < cfg['canvas']['width'] - 2 * cfg['paddleWidth'] - cfg['ballSize']
         and gs['ballY'] + cfg['ballSize'] >= gs['rightPaddleY']
         and gs['ballY'] <= gs['rightPaddleY'] + cfg['paddleHeight']
         and gs['ballSpeedX'] > 0)
    ):
      # check correct ball direction
      if ((gs['ballSpeedY'] > 0 and gs['ballY'] < gs['leftPaddleY'] + cfg['paddleHeight'] / 2) or
          (gs['ballSpeedY'] < 0 and gs['ballY'] > gs['leftPaddleY'] + cfg['paddleHeight'] / 2)):
        lastContactFrame = frameCount
        gs['ballSpeedY'] = -getRandomInt(4, 8) if gs['ballSpeedY'] > 0 else getRandomInt(4, 8)


def check_ball_outofbounds(gs, cfg):
  # Check if the ball is out of bounds
  if gs['ballX'] < 0:
    logger.debug("PongCalcLocal > Ball is out of bounds")
    gs['scorePlayer2'] += 1
    return True
  elif gs['ballX'] >= cfg['canvas']['width'] - cfg['ballSize']:
    logger.debug("PongCalcLocal > Ball is out of bounds")
    gs['scorePlayer1'] += 1
    return True
  return False

def reset_ball_position(gs, cfg):
  logger.debug("PongCalcLocal > reset_ball_position")
  gs['ballX'] = cfg['canvas']['width'] / 2
  gs['ballY'] = getRandomInt(-125, 125) + cfg['canvas']['height'] / 2
  gs['ballSpeedX'] = -getRandomInt(4, 6) if gs['ballSpeedX'] > 0 else getRandomInt(4, 6)
  gs['ballSpeedY'] = -getRandomInt(1, 3) if gs['ballSpeedY'] > 0 else getRandomInt(1, 3)

