import os, json, logging, websockets, ssl, asyncio, aiohttp
from channels.generic.websocket import AsyncWebsocketConsumer
from django.template.loader import render_to_string
from .utils import getUserId, getUserData, asyncRequest, get_player_language, send_data_via_websocket
from django.utils.translation import activate, gettext as _

import prettyprinter
from prettyprinter import pformat
prettyprinter.set_default_config(depth=None, width=80, ribbon_width=80)

logger = logging.getLogger(__name__)
logging.getLogger('websockets').setLevel(logging.WARNING)

class ProxyCalcGameTournament(AsyncWebsocketConsumer):
    async def connect(self):
        logger.debug("ProxyCalcGameTournament > connect")
        await self.accept()
        
        # Extract the query selector from the WebSocket URL
        query_selector = self.scope['query_string'].decode('utf-8')
        if '=' in query_selector and len(query_selector.split('=')) > 1:
            game_type = query_selector.split('=')[1]
        else:
            game_type = None
        
        if game_type == None or game_type not in ['pong', 'cows']:
            logger.error("ProxyCalcGameTournament > No game_type provided, connection closed")
            await self.close()
            return
        
        # Create an SSL context that explicitly trusts the calcgame certificate
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context.load_verify_locations(os.getenv("CERTFILE"))

        # Establish the WebSocket connection with the trusted certificate
        self.calcgame_ws = await websockets.connect(
            f"wss://calcgame:9004/pongcalc_consumer/local/{game_type}/",
            ssl=ssl_context
        )

        # Listener Loop as background task that listens for messages from the calcgame WebSocket and sends those updates to the client. 
        self.calcgame_task = asyncio.create_task(self.listen_to_calcgame())

    async def disconnect(self, close_code):
        logger.debug("ProxyCalcGameTournament > disconnect")
        # Close the WebSocket connection to the calcgame service
        if self.calcgame_ws:
            await self.calcgame_ws.close()

        # Cancel the background task listening to calcgame
        if hasattr(self, 'calcgame_task'):
            self.calcgame_task.cancel()

    async def receive(self, text_data):
        # Handle messages received from the client
        logger.debug("ProxyCalcGameTournament > receive from client")
        
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            return
    
        # save the player names and context to build html later
        if data['type'] == 'opening_connection, game details':
            
            jwt_token = self.scope['cookies']['jwt_token']
            user_id = await getUserId(jwt_token)
            user = await getUserData(user_id)

            logger.debug(f"ProxyCalcGameTournament > getUserData: {pformat(user)}")

            self.context = {
                'user': user,
                'session': self.scope['session'],
                'cookies': self.scope['cookies'],
            }

            p1_id = self.context['user']['user_id']

            self.trmt_info = {
                'tournament_id': 0,
                'game_type': data['game_type'],
                'game_round': data['game_round'],
                'p1_name': data['p1_name'],
                'p2_name': data['p2_name'],
                'p3_name': data['p3_name'],
                'p4_name': data['p4_name'],
                'p1_id': p1_id,
                'p2_id': 0,
                'p3_id': 0,
                'p4_id': 0,
            }

            if p1_id != 0:
                user_data = await getUserData(p1_id)
                self.trmt_info['p1_avatar_url'] = user_data['avatar_url']

            logger.debug(f"ProxyCalcGameTournament > opening_connection with players: {self.trmt_info['p1_name']}, {self.trmt_info['p2_name']}, {self.trmt_info['p3_name']}, {self.trmt_info['p4_name']}")

            # Create a new tournament and retrieve next game info
            next_game_info = await self.createTournament()
            
            if next_game_info['status'] == 'error':
                await self.send(json.dumps({
                    'type': 'error',
                    'message': next_game_info['message']
                }))
                return
            
            self.trmt_info['tournament_id'] = next_game_info['info']['tournament_id']

            player_language = get_player_language(self.context)
            activate(player_language)

            logger.debug(f"ProxyCalcGameTournament > tournament_id: {self.trmt_info['tournament_id']}")
            if next_game_info['info']['game_round_title'] == 'Semi-Final 1':
                game_round_title = _('Semi-Final 1')
            if next_game_info['info']['game_round_title'] == 'Semi-Final 2':
                game_round_title = _('Semi-Final 2')
            if next_game_info['info']['game_round_title'] == 'Final':
                game_round_title = _('Final')
            
            logger.debug(f"ProxyCalcGameTournament > next_game_info['info']['game_round_title']: {next_game_info['info']['game_round_title']}, game_round_title: {game_round_title}")

            self.game_info = {
                'tournament_id': self.trmt_info['tournament_id'],
                'game_round': next_game_info['info']['game_round'],
                'game_round_title': game_round_title,
                'game_type': self.trmt_info['game_type'],
                'p1_name': next_game_info['info']['p1_name'],
                'p2_name': next_game_info['info']['p2_name'],
                'p1_id': next_game_info['info']['p1_id'],
                'p2_id': next_game_info['info']['p2_id'],
            }
            if next_game_info['info']['p1_id'] != 0 or next_game_info['info']['p2_id'] != 0:
                self.game_info['notify_player'] = ", " + _("you play next in the tournament")
            
            if next_game_info['info']['p1_id'] != 0:
                self.game_info['p1_avatar_url'] = self.trmt_info['p1_avatar_url']
            if next_game_info['info']['p2_id'] != 0:
                self.game_info['p2_avatar_url'] = self.trmt_info['p1_avatar_url']

            logger.debug(f"ProxyCalcGameTournament > self.game_info: {pformat(self.game_info)}")

            html = render_to_string('fragments/tournament_start_fragment.html', {'context': self.context, 'info': self.game_info})

            logger.debug(f"ProxyCalcGameTournament > sending game_start page to client")
            await self.send(json.dumps({
                'type': 'game_start',
                'message': 'Game starting...',
                'html': html,
                'info': self.game_info,
            }))

            self.game_info['type'] = 'opening_connection, game details'
            await send_data_via_websocket(self.calcgame_ws, json.dumps(self.game_info))
            
            return

        elif data['type'] == 'next_game, game details':
            # Create an SSL context that explicitly trusts the calcgame certificate
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_context.load_verify_locations(os.getenv("CERTFILE"))

            # Establish the WebSocket connection with the trusted certificate
            self.calcgame_ws = await websockets.connect(
                f"wss://calcgame:9004/pongcalc_consumer/local/{self.trmt_info['game_type']}/",
                ssl=ssl_context
            )

            # Listener Loop as background task that listens for messages from the calcgame WebSocket and sends those updates to the client. 
            self.calcgame_task = asyncio.create_task(self.listen_to_calcgame())

        # Forward the message from the client to the calcgame WebSocket server
        await send_data_via_websocket(self.calcgame_ws, text_data)
    
    async def createTournament(self):
        logger.debug("ProxyCalcGameTournament > createTournament")
        play_url = 'https://play:9003/api/createTournament/'
        csrf_token = self.context['cookies'].get('csrftoken')
        data = self.trmt_info

        # Make request to play container to create tournament
        response_json = await asyncRequest("POST", csrf_token, play_url, data)
        return response_json

    async def listen_to_calcgame(self):
        try:
            while True:
                # Continuously receive messages from calcgame and pass to client
                calcgame_response = await self.calcgame_ws.recv()
                data = json.loads(calcgame_response)

                if not data['type'] == 'game_update' and data['message']:
                    logger.debug(f"ProxyCalcGameTournament > from calcgame: {data['message']}")

                if data['type'] == 'game_end':
                    # Game ended
                    await self.game_end(calcgame_response)
                    break
                else:
                    await self.send(calcgame_response)

        except websockets.exceptions.ConnectionClosed:
            logger.debug("ProxyCalcGameTournament > calcgame connection closed")
            pass

    async def game_end(self, calcgame_response):
        logger.debug("ProxyCalcGameTournament > game_end")
        data_calcgame_response = json.loads(calcgame_response)
        game_result = data_calcgame_response.get('game_result')
        logger.debug(f"ProxyCalcGameTournament > game_end game_result: {game_result}")

        # Update tournament -save game result in database and get next game
        response = await self.update_tournament(game_result)
        if response['status'] == 'error':
            await self.send(json.dumps({
                'type': 'error',
                'message': response['message']
            }))
            return
        
        # if response['message'] == 'tournament ended':
        if response['message'].find('Tournament ended') != -1:
            logger.debug("ProxyCalcGameTournament > tournament ended")
            await self.tournament_end(response)
            return
        
        response['info']['previous_p1_name'] = self.game_info['p1_name']
        response['info']['previous_p2_name'] = self.game_info['p2_name']

        player_language = get_player_language(self.context)
        activate(player_language)

        logger.debug(f"ProxyCalcGameTournament > tournament_id: {self.trmt_info['tournament_id']}")
        if response['info']['game_round'] == 'Semi-Final 2':
            game_round_title = _('Semi-Final 2')
        if response['info']['game_round'] == 'Final':
            game_round_title = _('Final')
        response['info']['game_round_title'] = game_round_title

        # Update game_info with next game info
        self.game_info['game_round'] = response['info']['game_round']
        self.game_info['game_round_title'] = game_round_title,
        self.game_info['p1_name'] = response['info']['p1_name']
        self.game_info['p2_name'] = response['info']['p2_name']
        self.game_info['p1_id'] = response['info']['p1_id']
        self.game_info['p2_id'] = response['info']['p2_id']

        if response['info']['p1_id'] != 0:
            response['info']['p1_avatar_url'] = self.trmt_info['p1_avatar_url']
            response['info']['notify_player'] = ", " + _("you play next in the tournament")
        elif response['info']['p2_id'] != 0:
            response['info']['p2_avatar_url'] = self.trmt_info['p1_avatar_url']
            response['info']['notify_player'] = ", " + _("you play next in the tournament")        

        html = render_to_string('fragments/tournament_next_game_fragment.html',
                                {
                                  'context': self.context,
                                  'game_result': game_result,
                                  'info': response['info']
                                })
        data_calcgame_response['html'] = html
        data_calcgame_response['info'] = response['info']
        
        # Notify player game has ended and send next tournament game html
        await self.send(json.dumps(data_calcgame_response))

        # Close websocket connection to calcgame
        await self.calcgame_ws.close()
        self.calcgame_task.cancel()

        

    async def update_tournament(self, game_result):
        logger.debug("ProxyCalcGameTournament > update_tournament")
        # Save game to database
        play_url = 'https://play:9003/api/updateTournament/'

        csrf_token = self.context['cookies'].get('csrftoken') 
        
        data = {
            'tournament_id': self.trmt_info['tournament_id'],
            'game_type': self.trmt_info['game_type'],
            'game_round':  self.game_info['game_round'],
            'p1_name': self.game_info['p1_name'],
            'p2_name': self.game_info['p2_name'],
            'p1_id': self.game_info['p1_id'],
            'p2_id': self.game_info['p2_id'],
            'p1_score': game_result.get('p1_score'),
            'p2_score': game_result.get('p2_score'),
            'game_winner_name': game_result.get('game_winner_name'),
            'game_winner_id': self.game_info['p1_id'] if game_result.get('game_winner_name') == self.game_info['p1_name'] else self.game_info['p2_id'],
        }

        logger.debug(f"ProxyCalcGameTournament > update_tournament data: {pformat(data)}")
        
        response_json = await asyncRequest("POST", csrf_token, play_url, data)
        return response_json
    

    async def tournament_end(self, response):        
        # Notify player that tournament has ended and send tournament_end html
        logger.debug(f"ProxyCalcGameTournament > tournament_end response: {pformat(response)}")

        player_language = get_player_language(self.context)
        activate(player_language)
        html = render_to_string('fragments/tournament_end_fragment.html',
                                {
                                    'context': self.context,
                                    'info': response['info']
                                })

        response = {
            'status': 'success',
            'type': 'tournament_end',
            'info': response['info'],
            'html': html,
        }
        await self.send(json.dumps(response))