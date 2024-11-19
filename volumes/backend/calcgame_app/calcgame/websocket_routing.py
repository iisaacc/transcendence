from django.urls import path, re_path
from . import consumersCalcPongLocal, consumersCalcPongRemote, consumersCalcCowsLocal, consumersCalcCowsRemote

websocket_urlpatterns = [
    path('pongcalc_consumer/local/pong/', consumersCalcPongLocal.PongCalcLocal.as_asgi()),
    path('pongcalc_consumer/local/cows/', consumersCalcCowsLocal.CowsCalcLocal.as_asgi()),
    path('pongcalc_consumer/remote/pong/', consumersCalcPongRemote.PongCalcRemote.as_asgi()),
    path('pongcalc_consumer/remote/cows/', consumersCalcCowsRemote.CowsCalcRemote.as_asgi()),
    # re_path(r'pongcalc_consumer/$', consumers.PongCalcConsumer.as_asgi()),
]
