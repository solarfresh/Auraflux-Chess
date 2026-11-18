class AgentConfigNotFoundError(Exception):
    """Raised when the specified AgentConfig is not found."""
    def __init__(self, name):
        self.name = name
        super().__init__(f"Agent configuration {name} not found")
