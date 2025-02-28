import json

from channels.generic.websocket import AsyncWebsocketConsumer

from django.contrib.auth.models import AnonymousUser
from .models import Notification, Teacher, AppUser, StudentNotification

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        username = text_data_json["username"]
        timestamp = text_data_json["timestamp"]

        await self.channel_layer.group_send(
            self.room_group_name, {
                "type": "chat_message",
                "message": message,
                "username": username,
                "timestamp": timestamp
            }
        )

    async def chat_message(self, event):
        message = event["message"]
        username = event["username"]
        timestamp = event["timestamp"]

        await self.send(text_data=json.dumps({
            "message": message,
            "username": username,
            "timestamp": timestamp
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close()
            return

        app_user = await self.get_app_user(user)

        if app_user and app_user.account_type == 'T':  # Only allow teachers
            self.group_name = f"notifications_{user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass  # No need to handle incoming messages from the client.

    async def send_notification(self, event):
        notification = event["message"]
        await self.send(text_data=json.dumps({"message": notification}))

    async def get_app_user(self, user):
        return await AppUser.objects.select_related("user").filter(user=user).afirst()

class StudentNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            print("WebSocket rejected: User is not authenticated.")
            await self.close()
            return

        # Get the AppUser linked to this Django User
        try:
            app_user = await AppUser.objects.select_related("user").aget(user=user)
        except AppUser.DoesNotExist:
            print("WebSocket rejected: No AppUser found.")
            await self.close()
            return

        if app_user.account_type == 'S':  # Only allow students
            self.group_name = f"notifications_student_{user.id}"
            print(f"WebSocket connected: {self.group_name}")
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            print("WebSocket rejected: User is not a student.")
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            print(f"WebSocket disconnected: {self.group_name}")

    async def send_student_notification(self, event):
        notification = event["message"]
        await self.send(text_data=json.dumps({"message": notification}))