# Realtime Application

The `realtime` application provides WebSocket-based communication to deliver real-time notifications to authenticated users.

## WebSocket Endpoint

- **URL**: `/ws/notifications/`
- **Authentication**: Requires a valid, authenticated user session.
- **Protocol**: WebSocket

## Functionality

- This application uses Django Channels (`channels`) to handle persistent WebSocket connections.
- Upon successful authentication and connection, the client is subscribed to a personal notification group based on their user ID (`user_<user_id>`).
- The server pushes notifications to the client through the `send_notification` method in the consumer.
- Utility functions (`send_ws_notification`) allow backend tasks or services to easily send notifications to specific users via the channel layer.

## Usage

### 1. Connecting via Client (JavaScript / Frontend)

```javascript
const ws = new WebSocket(`ws://${window.location.host}/ws/notifications/`);

ws.onopen = function(event) {
    console.log("Connected to notification WebSocket.");
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log("Received event:", data.event_type);
    console.log("Payload:", data.payload);
};

ws.onclose = function(event) {
    console.log("Disconnected from notification WebSocket.");
};
```

### 2. Sending Notifications from Backend

You can use the helper function `send_ws_notification` from `api.realtime.utils`:

```python
from api.realtime.utils import send_ws_notification

# Send notification to a specific user
send_ws_notification(
    user_id=user.id,
    event_type="agent_task_completed",
    payload={"task_id": "12345", "result": "success"}
)
```

### Message Format

The notifications received by the client are formatted as JSON:

```json
{
  "event_type": "string",
  "status": "success",
  "payload": {
    "key": "value"
  }
}
```
