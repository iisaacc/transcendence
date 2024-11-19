import os, json, logging, websockets, ssl, asyncio, aiohttp, jwt, random, requests
from django.conf import settings

import prettyprinter
from prettyprinter import pformat
prettyprinter.set_default_config(depth=None, width=80, ribbon_width=80)

logger = logging.getLogger(__name__)
logging.getLogger('websockets').setLevel(logging.WARNING)

used_ids = set()
def generate_unique_id():
    while True:
        id = random.randint(1, 1000000)
        if id not in used_ids:
            used_ids.add(id)
            return id


async def getDecodedJWT(jwt_token):
    decoded_data = jwt.decode(
        jwt_token,
        settings.SECRET_KEY,
        algorithms=["HS256"]
    )
    return decoded_data

# Get user_id from JWT token
async def getUserId(jwt_token):
    try:
        decoded_data = await getDecodedJWT(jwt_token)
    except Exception as e:
        logger.error(f"getUserId > Error decoding JWT: {e}")
        return 0
    user_id = decoded_data['user_id']
    return user_id
    
# Get user data from user_id
async def getUserData(user_id):
    user = {
        'user_id': user_id,
        'username': None,
        'avatar_url': None,
        'profile': {},
    }
    # logger.debug(f"getUserData > user_id: {user_id}")
    if user_id == 0:
      return user

    url = 'https://authentif:9001/api/getUserInfo/' + str(user_id) + '/'

    response = await asyncRequest("GET", "", url, "")
    if response.get('status') == 'success':
        user['username'] = response.get('username')
        user['avatar_url'] = response.get('avatar_url')

    url = 'https://profileapi:9002/api/profile/' + str(user_id) + '/'

    response = await asyncRequest("GET", "", url, "")
    if response.get('status') != 'error':
        user['profile'] = response

    return user


async def getUserProfileAsync(user_id):
    url = 'https://profileapi:9002/api/profile/' + str(user_id) + '/'

    response = await asyncRequest("GET", "", url, "")
    return response

def getUserProfile(user_id):
    url = 'https://profileapi:9002/api/profile/' + str(user_id) + '/'

    response = requests.get(url, verify=os.getenv("CERTFILE"))
    return response.json()
    

# Async http request, csrf_token and data can be "" for 'GET' requests
async def asyncRequest(method, csrf_token, url, data):
    headers = {
        'X-CSRFToken': csrf_token,
        'Cookie': f'csrftoken={csrf_token}',
        'Content-Type': 'application/json',
        'Referer': 'https://gateway:8443',
    }
            
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.load_verify_locations(os.getenv("CERTFILE"))

    # async http request
    if method == "GET":
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, ssl=ssl_context) as response:
                    response_json = await response.json()
                    logger.debug(f"asyncRequest > get response: {response_json.get('message')}")
            except aiohttp.ClientError as e:
                logger.error(f"asyncRequest > Error during request: {e}")
                return None
          
    elif method == "POST":
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=data, headers=headers, ssl=ssl_context) as response:
                    response_json = await response.json()
                    logger.debug(f"asyncRequest > post response: {response_json.get('message')}")
            except aiohttp.ClientError as e:
                logger.error(f"asyncRequest > Error during request: {e}")
                return None
            
    else:
        logger.error(f"asyncRequest > Unknown method: {method}")
        return None
    
    return response_json


def get_player_language(context):
    cookies = context.get('cookies', {})
    user = context.get('user', {})
    profile = user.get('profile', {})
    
    # Check for language in cookies
    if 'django_language' in cookies and len(cookies['django_language']) == 2:
        return cookies['django_language']
    
    # Check for preferred language in profile
    if 'preferred_language' in profile:
        return profile['preferred_language']
    
    # Default to 'en'
    return 'en'

# Send data via websocket checking if connection is open
async def send_data_via_websocket(ws, data):
    if ws and ws.state == websockets.protocol.State.OPEN:
        try:
            await ws.send(data)
        except websockets.exceptions.ConnectionClosed as e:
            logger.error(f"WebSocket connection closed: {e}")
    else:
        logger.error("WebSocket connection is not open.")

def getDjangoLanguageCookie(request):
    django_language = ''
    if 'django_language' in request.COOKIES and len(request.COOKIES['django_language']) == 2:
        django_language = request.COOKIES['django_language']
    if django_language not in ['en', 'fr', 'es']:
        django_language = 'en'
    return django_language