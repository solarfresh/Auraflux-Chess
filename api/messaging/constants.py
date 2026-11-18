class Queue:
    CHESS = 'chess'
    AGENT = 'agent'


class AgentRequest:
    name = "handle_agent_request"
    queue = Queue.AGENT


class EmbeddingRequest:
    name = "handle_embedding_request"
    queue = Queue.AGENT
