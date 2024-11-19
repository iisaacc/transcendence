import os, json, logging, websockets, ssl, asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.template.loader import render_to_string
from .utils import getUserId, getUserData, asyncRequest, get_player_language, send_data_via_websocket
from django.utils.translation import activate, gettext as _

import prettyprinter
from prettyprinter import pformat
prettyprinter.set_default_config(depth=None, width=80, ribbon_width=80)

logger = logging.getLogger(__name__)
logging.getLogger('websockets').setLevel(logging.WARNING)


class ProxyCalcGameLocal(AsyncWebsocketConsumer):
    async def connect(self):
        logger.debug("ProxyCalcGameLocal > connect")
        await self.accept()
        
        # Extract the query selector from the WebSocket URL
        query_selector = self.scope['query_string'].decode('utf-8')
        if '=' in query_selector and len(query_selector.split('=')) > 1:
            game_type = query_selector.split('=')[1]
        else:
            game_type = None
        
        if game_type == None or game_type not in ['pong', 'cows']:
            logger.error("ProxyCalcGameRemote > No game_type provided, connection closed")
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
        logger.debug("ProxyCalcGameLocal > disconnect")
        # Close the WebSocket connection to the calcgame service
        if self.calcgame_ws:
            await self.calcgame_ws.close()

        # Cancel the background task listening to calcgame
        if hasattr(self, 'calcgame_task'):
            self.calcgame_task.cancel()

    async def receive(self, text_data):
        # Handle messages received from the client
        logger.debug("ProxyCalcGameLocal > receive from client")
        
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            return
        
        # save the player names and context to build html later
        if data['type'] == 'opening_connection, game details':
            self.p1_name = data['p1_name']
            self.p2_name = data['p2_name']
            self.game_type = data['game_type']
            jwt_token = self.scope['cookies']['jwt_token']
            user_id = await getUserId(jwt_token)
            user = await getUserData(user_id)
            self.context = {
                'user': user,
                'session': self.scope['session'],
                'cookies': self.scope['cookies'],
            }
            logger.debug(f"ProxyCalcGameLocal > opening_connection with players: {self.p1_name}, {self.p2_name}")

            logger.debug(f"ProxyCalcGameLocal > self.context['user']: {self.context['user']}, ['user']['user_id']: {self.context['user']['user_id']}")

            self.p1_id = self.context['user']['user_id'] if self.context['user']['user_id'] else 0
            self.p2_id = 0
            info = {
                'tournament_id': 0,
                'game_round': 'single',
                'game_type': self.game_type,
                'p1_name': self.p1_name,
                'p2_name': self.p2_name,
                'p1_id': self.p1_id,
                'p2_id': self.p2_id,
            }
            
            logger.debug(f"ProxyCalcGameLocal > user: {pformat(user)}")

            player_language = get_player_language(self.context)
            activate(player_language)
            html = render_to_string('fragments/game_fragment.html', {'context': self.context, 'info': info})
            logger.debug(f"ProxyCalcGameLocal > sending game_start page to client")
            await self.send(json.dumps({
                'type': 'game_start',
                'message': 'Game starting...',
                'html': html,
            }))
        # Forward the message from the client to the calcgame WebSocket server
        await send_data_via_websocket(self.calcgame_ws, text_data)

    async def listen_to_calcgame(self):
        try:
            while True:
                # Continuously receive messages from calcgame and pass to client
                calcgame_response = await self.calcgame_ws.recv()
                data = json.loads(calcgame_response)

                if not data['type'] == 'game_update' and data['message']:
                    logger.debug(f"ProxyCalcGameLocal > from calcgame: {data['message']}")

                if data['type'] == 'game_end':
                    # Game ended
                    await self.game_end(calcgame_response)
                    break
                else:
                    await self.send(calcgame_response)

        except websockets.exceptions.ConnectionClosed:
            logger.debug("ProxyCalcGameLocal > calcgame connection closed")
            pass

    async def game_end(self, calcgame_response):
        logger.debug("ProxyCalcGameLocal > game_end")
        data_calcgame_response = json.loads(calcgame_response)
        game_result = data_calcgame_response.get('game_result')
        logger.debug(f"ProxyCalcGameLocal > game_end game_result: {game_result}")

        player_language = get_player_language(self.context)
        activate(player_language)
        html = render_to_string('fragments/game_end_fragment.html', {
              'context': self.context,
              'game_result': game_result
            })
        data_calcgame_response['html'] = html

        # Save game to database
        await self.save_game_to_database(game_result)

        # Notify player that the game has ended and send game_end html
        await self.send(json.dumps(data_calcgame_response))
        

    async def save_game_to_database(self, game_result):
        logger.debug("ProxyCalcGameLocal > save_game_to_database")
        # Save game to database
        play_url = 'https://play:9003/api/saveGame/'
        csrf_token = self.context['cookies'].get('csrftoken') 
        
        data = {
            'game_type': self.game_type,
            'game_round': 'single',
            'p1_name': self.p1_name,
            'p2_name': self.p2_name,
            'p1_id': self.p1_id,
            'p2_id': self.p2_id,
            'p1_score': game_result.get('p1_score'),
            'p2_score': game_result.get('p2_score'),
            'game_winner_name': game_result.get('game_winner_name'),
            'game_winner_id': self.p1_id if game_result.get('game_winner_name') == self.p1_name else self.p2_id,
        }
        
        await asyncRequest("POST", csrf_token, play_url, data)
