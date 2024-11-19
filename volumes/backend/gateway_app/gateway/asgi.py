import os
from django.core.asgi import get_asgi_application
# from channels.http import AsgiHandler
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from . import websocket_routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gateway.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(), # through django
    # "http": AsgiHandler(), # through channels
    # "websocket": AllowedHostsOriginValidator(
    #     AuthMiddlewareStack(
    #       URLRouter(
    #           websocket_routing.websocket_urlpatterns
    #       )
    #     )
    # ),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_routing.websocket_urlpatterns
        )
    ),
})