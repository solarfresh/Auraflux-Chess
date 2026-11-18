# Messaging Module Usage Guidelines

This module implements an event-driven asynchronous architecture using `publish_event`.

## Core Invocation Logic

All external operation requests (e.g., AI inference, node processing) should be encapsulated as an `AgentRequest` and sent via `publish_event` to the appropriate queue.

### Example Usage

```python
from messaging.tasks import publish_event
from messaging.constants import AgentRequest

publish_event.delay(
    event_type=AgentRequest.name,
    payload={
        'type': 'Decomposition',
        'config': { ... },
        'payload': { ... },
    },
    queue=AgentRequest.queue
)
```

### Payload Contract
Requests must include the following fields to comply with the unified agent contract:
- **type**: Agent type identifier (e.g., Decomposition, Hypothesis).
- **config**: Agent configuration dictionary.
- **payload**: Execution payload, including input data, etc.
- **next_event_type**: (Optional) Subsequent chained task.
- **next_event_payload**: (Optional) Data structure for the next step.
- **next_event_queue**: (Optional) Queue for the next task.
