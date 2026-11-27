class Queue:
    CHESS = 'chess'
    AGENT = 'agent'


class AgentRequest:
    name = "handle_agent_request"
    queue = Queue.AGENT


class EmbeddingRequest:
    name = "handle_embedding_request"
    queue = Queue.AGENT


class NodeActionRequest:
    name = "handle_node_action_request"
    queue = Queue.CHESS


class NodeActionPersistence:
    name = "handle_node_action_persistence"
    queue = Queue.CHESS
