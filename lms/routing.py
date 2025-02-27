from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/notifications/(?P<user_id>\d+)/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/notifications/student/(?P<user_id>\d+)/$', consumers.StudentNotificationConsumer.as_asgi()),
]
