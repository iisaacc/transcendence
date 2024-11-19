from django.urls import path, re_path
from .consumers import FormConsumer
from . import consumerProxyCalcGameLocal, consumerProxyCalcGameRemote, consumerProxyCalcGameTournament, consumerProxyCalcGameInvite, consumerMainRoom

websocket_urlpatterns = [
    # path('wss/calcgame/local/', consumerProxyCalcGameLocal.ProxyCalcGameLocal.as_asgi()),
    path('wss/calcgame/remote/', consumerProxyCalcGameRemote.ProxyCalcGameRemote.as_asgi()),
    re_path(r'wss/calcgame/local/$', consumerProxyCalcGameLocal.ProxyCalcGameLocal.as_asgi()),
    re_path(r'wss/calcgame/tournament/$', consumerProxyCalcGameTournament.ProxyCalcGameTournament.as_asgi()),
    path('wss/calcgame/invite/', consumerProxyCalcGameInvite.ProxyCalcGameInvite.as_asgi()),

    # Friend Invite suggestion
    path('wss/inviteafriend', FormConsumer.as_asgi()),
    path('wss/inviteafriend/', FormConsumer.as_asgi()),

    # Main room
    path('wss/mainroom/<int:user_id>/', consumerMainRoom.mainRoom.as_asgi()),
    # re_path(r'ws/somepath/$', consumers.YourConsumer.as_asgi()),
]
