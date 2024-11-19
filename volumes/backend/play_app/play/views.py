import os, json, requests, logging
from django.utils import timezone
from django.http import JsonResponse
from django.db import DatabaseError
from django.forms.models import model_to_dict
from asgiref.sync import sync_to_async
from .models import Game, Tournament
from .viewsBlockchain import save_tournament_results_in_blockchain, create_tournament_in_blockchain
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)
import prettyprinter
from prettyprinter import pformat
prettyprinter.set_default_config(depth=None, width=80, ribbon_width=80)

def api_saveGame(request):
    logger.debug("api_saveGame")
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.debug(f'api_saveGame > Received data: {data}')
            logger.debug(f'game_winner_name: {data.get("game_winner_name")}, id: {data.get("game_winner_id")}')
            logger.debug('api_saveGame > Saving game...')
            game = Game.objects.create(
                game_type = data.get('game_type'),
                game_round = data.get('game_round'),
                p1_name = data.get('p1_name'),
                p2_name = data.get('p2_name'),
                p1_id = data.get('p1_id'),
                p2_id = data.get('p2_id'),
                p1_score = data.get('p1_score'),
                p2_score = data.get('p2_score'),
                game_winner_name = data.get('game_winner_name'),
                game_winner_id = data.get('game_winner_id')
            )
            logger.debug('api_saveGame > Game saved')

            info = {
                'tournament_id': 0,
                'game_type': data.get('game_type'),
                'game_round': 'single',
                'p1_name': data.get('p1_name'),
                'p2_name': data.get('p2_name'),
                'p1_id': data.get('p1_id'),
                'p2_id': data.get('p2_id'),
                'previous_round': 'single',
                'previous_winner_name': data.get('game_winner_name'),
                'previous_p1_score': data.get('p1_score'),
                'previous_p2_score': data.get('p2_score'),
            }
            return JsonResponse({'status': 'success', 'message': 'Game saved', 'info': info})
        except (json.JSONDecodeError, DatabaseError) as e:
            logger.debug(f'api_saveGame > Error: {str(e)}')
            return JsonResponse({'status': 'error', 'message': 'Error: ' + str(e)}, status=400)

    logger.debug('api_saveGame > Method not allowed')
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


def api_createTournament(request):
    logger.debug("api_createTournament")
    if request.method == 'POST':
        try:
          data = json.loads(request.body)
          logger.debug(f'api_createTournament > Received data: {data}')

          logger.debug('api_createTournament > Creating tournament...')
          tournament = Tournament.objects.create(
              game_type = data.get('game_type'),
              t_p1_name = data.get('p1_name'),
              t_p2_name = data.get('p2_name'),
              t_p3_name = data.get('p3_name'),
              t_p4_name = data.get('p4_name'),
              t_p1_id = data.get('p1_id'),
              t_p2_id = data.get('p2_id'),
              t_p3_id = data.get('p3_id'),
              t_p4_id = data.get('p4_id')
          )
          logger.debug(f'api_createTournament > Starting tournament: {tournament}')
          tournament.start_tournament()
          
          info = {
              'tournament_id': tournament.id,
              'game_round': 'Semi-Final 1',
              'game_round_title': 'Semi-Final 1', # don't translate
              'p1_name': Game.objects.get(id=tournament.semifinal1.id).p1_name, 
              'p2_name': Game.objects.get(id=tournament.semifinal1.id).p2_name,
              'p1_id': Game.objects.get(id=tournament.semifinal1.id).p1_id,
              'p2_id': Game.objects.get(id=tournament.semifinal1.id).p2_id,
          }

          message = ("starting Semi-Final 1")

          return JsonResponse({'status': 'success', 'message': message, 'info': info})
        except (json.JSONDecodeError, DatabaseError) as e:
            logger.debug(f'api_createTournament > Error: {str(e)}')
            return JsonResponse({'status': 'error', 'message': 'Error: ' + str(e)}, status=400)
    logger.debug('api_createTournament > Method not allowed')
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


def api_updateTournament(request):
    logger.debug("api_updateTournament")
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.debug(f'api_updateTournament > Received data: {data}')
            tournament_id = data.get('tournament_id')
            game_round = data.get('game_round')
            p1_score = data.get('p1_score')
            p2_score = data.get('p2_score')
            game_winner_name = data.get('game_winner_name')
            game_winner_id = data.get('game_winner_id')

            logger.debug(f'api_updateTournament > tournament_id: {tournament_id}, game_round: {game_round}, p1_score: {p1_score}, p2_score: {p2_score}, game_winner_name: {game_winner_name}, game_winner_id: {game_winner_id}')

            tournament = Tournament.objects.get(id=tournament_id)
            logger.debug(f'api_updateTournament > Tournament: {tournament}')
            logger.debug(f'api_updateTournament > current game_round: {game_round}')

            # Get the game to update the score of
            if game_round == 'Semi-Final 1':
                game = tournament.semifinal1
            elif game_round == 'Semi-Final 2':
                game = tournament.semifinal2
            elif game_round == 'Final':
                game = tournament.final

            logger.debug(f'api_updateTournament > Game {game.id} before: {game}')
            # Update the game
            game = Game.objects.get(id=game.id)
            game.p1_score = p1_score
            game.p2_score = p2_score
            game.game_winner_name = game_winner_name
            game.game_winner_id = game_winner_id
            game.date = timezone.now()
            game.save()
            logger.debug(f'api_updateTournament > Game {game.id} after : {game}')
            tournament = Tournament.objects.get(id=tournament_id)

            # Check the tournament's progress and advance if needed

            # If SF1, start SF2
            if game_round == 'Semi-Final 1':
              game_round = 'Semi-Final 2'
              info = {
                  'tournament_id': tournament.id,
                  'game_round': game_round,
                  'game_round_title': 'Semi-Final 2', # don't translate
                  'p1_name': Game.objects.get(id=tournament.semifinal2.id).p1_name,
                  'p2_name': Game.objects.get(id=tournament.semifinal2.id).p2_name,
                  'p1_id': Game.objects.get(id=tournament.semifinal2.id).p1_id,
                  'p2_id': Game.objects.get(id=tournament.semifinal2.id).p2_id,
                  'previous_round': 'Semi-Final 1',
                  'previous_winner_name': game_winner_name,
                  'previous_p1_name': data.get('p1_name'),
                  'previous_p2_name': data.get('p2_name'),
                  'previous_p1_score': p1_score,
                  'previous_p2_score': p2_score,
              }
              message = ("starting Semi-Final 2")
            # If SF2, start Final
            elif game_round == 'Semi-Final 2':
              tournament.create_final()
              game_round = 'Final'
              info = {
                  'tournament_id': tournament.id,
                  'game_round': game_round,
                  'game_round_title': 'Final', # don't translate
                  'p1_name': tournament.semifinal1.game_winner_name,
                  'p2_name': tournament.semifinal2.game_winner_name,
                  'p1_id': tournament.semifinal1.game_winner_id,
                  'p2_id': tournament.semifinal2.game_winner_id,
                  'previous_round': 'Semi-Final 2',
                  'previous_winner_name': game_winner_name,
                  'previous_p1_name': tournament.semifinal2.p1_name,
                  'previous_p2_name': tournament.semifinal2.p2_name,
                  'previous_p1_score': p1_score,
                  'previous_p2_score': p2_score,
              }
              message = ("starting Final")
            # If Final, end Tournament
            elif game_round == 'Final':
              tournament.date_finished = timezone.now()
              tournament.t_winner_name = game_winner_name
              tournament.t_winner_id = game_winner_id
              tournament.save()
              game_round = 'has_ended'
              tournament = Tournament.objects.get(id=tournament_id)
              info = {
                  'tournament': model_to_dict(tournament),
                  'game_round': game_round
              }
              # Save the results in the blockchain
              blockchain_response = json.loads(save_tournament_results_in_blockchain(tournament, game_winner_name))
              message = blockchain_response.get('message')
              # message = ("tournament ended")
            logger.debug(f'api_updateTournament > {game_round}: {message}')
            logger.debug(f'api_updateTournament > info: {info}')

            return JsonResponse({'status': 'success', 'message': message, 'info': info})
        except (json.JSONDecodeError, DatabaseError) as e:
            logger.debug(f'api_updateTournament > Error: {str(e)}')
            return JsonResponse({'status': 'error', 'message': 'Error: ' + str(e)}, status=400)
    logger.debug('api_updateTournament > Method not allowed')
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


def api_getUserStats(request, user_id, raw=False):
    logger.debug("api_getUserStats")
    if request.method != 'GET':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    try:
        games = Game.objects.filter(p1_id=user_id) | Game.objects.filter(p2_id=user_id)
        games_list = []
        for game in games:
            game_dict = (model_to_dict(game))
            game_dict['date'] = game.date.strftime('%Y-%m-%d %H:%M:%S')
            games_list.append(game_dict)
    except (json.JSONDecodeError, DatabaseError) as e:
        return JsonResponse({'status': 'error', 'message': 'Error: ' + str(e)}, status=400)
    if games_list is None:
        logger.debug("get_match_history > No games_list found")
        games_list = []
    
    total_games = 0
    wins = 0
    game_registry = []
    for game in games_list:
        game_winner_id = game.get('game_winner_id')
        if game_winner_id is not None:
            total_games += 1
            game_winner_id = int(game_winner_id)
            user_id_int = int(user_id)
            if game_winner_id == user_id_int:
                wins += 1
            game_registry.append({
                'game_type': game['game_type'],
                'game_round': game['game_round'],
                'p1_name': game['p1_name'],
                'p2_name': game['p2_name'],
                'p1_score': game['p1_score'],
                'p2_score': game['p2_score'],
                'game_winner_name': game['game_winner_name'],
                'game_winner_id': game['game_winner_id'],
                'date': game['date']
            })

    defeats = total_games - wins
    total_score = wins * 50
    winrate = round((wins / total_games) * 100, 2) if total_games > 0 else 0
    games_data = {
        'total_games': total_games,
        'wins': wins,
        'defeats': defeats,
        'total_score': total_score,
        'winrate': winrate,
        'game_registry': game_registry
    }
    if raw:
        return {'status': 'success', 'games_data': games_data}
    return JsonResponse({'status': 'success', 'games_data': games_data})


def api_getUserGames(request, user_id):
    logger.debug("api_getUserGames")
    if request.method == 'GET':
        response = api_getUserStats(request, user_id)
        logger.debug(f'api_getUserGames > response: {response}')
        target_id = api_getMatchMaking(request, user_id)
        logger.debug(f'api_getUserGames > target_id: {target_id}')
        return response
    logger.debug('api_getUserGames > Method not allowed')
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


def api_getMatchMaking(request, user_id):
    logger.debug("api_getMatchMaking")
    response = requests.get('https://profileapi:9002/api/getUsersIds/', verify=os.getenv("CERTFILE"))
    users_ids = response.json()
    user_id = int(user_id)
    logger.debug(f'api_getMatchMaking > user_id: {user_id}')
    users_ids = [int(id) for id in users_ids]
    users_ids.remove(user_id)
    logger.debug(f'api_getMatchMaking > data: {users_ids}')
    request_user_stats = api_getUserStats(request, user_id, raw=True)
    request_winrate = request_user_stats['games_data']['winrate']
    target_winrate = 100
    target_id = None
    for id in users_ids :
        user_stats = api_getUserStats(request, id, raw=True)
        if user_stats['status'] == 'success':
            winrate_diff = abs(user_stats['games_data']['winrate'] - request_winrate)
            if winrate_diff < target_winrate:
                target_winrate = winrate_diff
                target_id = id
        logger.debug(f'api_getMatchMaking > target_id: {target_id} with winrate difference: {target_winrate}')
    return JsonResponse({'status': 'success', 'target_id': target_id})


async def api_getWinrate(request, user_id, game_type):
  logger.debug("api_getWinrate")
  if user_id == '0':
    return JsonResponse({'status': 'success', 'winrate': 0})
  try:
    games = await sync_to_async(list)(Game.objects.filter(game_type=game_type).filter(p1_id=user_id) | Game.objects.filter(game_type=game_type).filter(p2_id=user_id))

    wins = 0
    total_games = 0
    for game in games:
      game_dict = model_to_dict(game)
      if str(game_dict['game_winner_id']) == user_id:
        wins += 1
      total_games += 1

    winrate = round((wins / total_games) * 100, 2) if total_games > 0 else 0
    logger.debug(f"api_getWinrate > wins: {wins}, total_games: {total_games}, winrate: {winrate}")
    return JsonResponse({'status': 'success', 'winrate': winrate})

  except (json.JSONDecodeError, DatabaseError) as e:
    return JsonResponse({'status': 'error', 'message': 'Error: ' + str(e)}, status=400)


def api_user_games(request, user_id):
    logger.debug("api_user_games")
    if request.method != 'GET':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        games = Game.objects.filter(p1_id=user_id) | Game.objects.filter(p2_id=user_id)
        games = games.filter(game_winner_name__isnull=False).order_by('-date')
        games_list = []
        for game in games:
            game_dict = (model_to_dict(game))
            game_dict['date'] = game.date.strftime('%Y-%m-%d %H:%M:%S')
            games_list.append(game_dict)
        
        tournaments = Tournament.objects.filter(t_p1_id=user_id) | Tournament.objects.filter(t_p2_id=user_id) | Tournament.objects.filter(t_p3_id=user_id) | Tournament.objects.filter(t_p4_id=user_id)
        tournaments = tournaments.filter(t_winner_name__isnull=False)
        # logger.debug(f"api_user_games > games_list: {pformat(games_list)}")
    except (json.JSONDecodeError, DatabaseError) as e:
        return JsonResponse({'status': 'error', 'message': 'Error: ' + str(e)}, status=400)
    
    pong_games = games.filter(game_type='pong')
    cows_games = games.filter(game_type='cows')
    data = {
      'pong': {
        'count': pong_games.count(),
        'wins': pong_games.filter(game_winner_id=user_id).count(),
        'losses': pong_games.exclude(game_winner_id=user_id).count(),
        'list': [game for game in games_list if game['game_type'] == 'pong'],
        't_count': tournaments.filter(game_type='pong').count(),
        't_wins': tournaments.filter(game_type='pong').filter(t_winner_id=user_id).count()
      },
      'cows': {
        'count': cows_games.count(),
        'wins': cows_games.filter(game_winner_id=user_id).count(),
        'losses': cows_games.exclude(game_winner_id=user_id).count(),
        'list': [game for game in games_list if game['game_type'] == 'cows'],
        't_count': tournaments.filter(game_type='cows').count(),
        't_wins': tournaments.filter(game_type='cows').filter(t_winner_id=user_id).count()
      },
      'games_list': games_list
    }
    
    data['pong']['winrate'] = round((data['pong']['wins'] / data['pong']['count']) * 100, 2) if data['pong']['count'] > 0 else 0

    data['cows']['winrate'] = round((data['cows']['wins'] / data['cows']['count']) * 100, 2) if data['cows']['count'] > 0 else 0

    # logger.debug(f"api_user_games > games_list: {pformat(data)}")
    return JsonResponse({'status': 'success', 'data': data})
