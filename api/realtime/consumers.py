import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

from .utils import get_user_group_name

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Handles generic WebSocket connections for an authenticated user to receive
    real-time notifications from background tasks across all applications (e.g., projects, agents).
    """

    async def connect(self):
        """
        Called when the WebSocket is handshaking as part of connection.
        Supports joining multiple groups (e.g., user-specific group and a global broadcast group).
        """
        user = self.scope.get("user")
        if user is None:
            logger.warning("Anonymous user attempted to connect to NotificationConsumer.")
            await self.close()
            return

        self.user_id = user.id
        self.user_group_name = get_user_group_name(self.user_id)

        # Define multiple groups to join (user group + global broadcast group)
        self.groups_to_join = [
            self.user_group_name,
            "broadcast_global_group"
        ]

        for group_name in self.groups_to_join:
            await self.channel_layer.group_add(
                group_name,
                self.channel_name
            )

        logger.info("User %s connected to WebSocket. Channels added to groups: %s",
                    self.user_id, self.groups_to_join)
        await self.accept()

    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes for any reason.
        Discards the connection from all joined groups.
        """
        if hasattr(self, 'groups_to_join'):
            for group_name in self.groups_to_join:
                await self.channel_layer.group_discard(
                    group_name,
                    self.channel_name
                )
            logger.info("User %s disconnected from WebSocket. Discarded from groups: %s",
                        getattr(self, 'user_id', 'Unknown'), self.groups_to_join)

    # --- Communication Methods ---

    async def broadcast_event(self, event):
        """
        Handles general broadcast messages sent to multiple channels/groups.
        """
        await self.send_notification(event)

    async def send_notification(self, event):
        """
        Receives a notification message from the worker via the Channels Layer
        and sends the data back to the client. This method is called when the
        worker uses {'type': 'send_notification'}.
        """
        event_type = event.get('event_type')
        payload = event.get('data', {})

        logger.debug("Received event '%s' for user %s. Sending to client.",
                     event_type, self.user_id)

        await self.send(text_data=json.dumps({
            'event_type': event_type,
            'status': event.get('status', 'success'),
            'payload': payload,
        }))

    async def receive(self, text_data=None, bytes_data=None):
        pass # Still keeping this empty for server-to-client transport
