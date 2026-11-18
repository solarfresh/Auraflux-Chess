from agents.models import AgentConfig, AgentConfigNotFoundError


class AgentConfigService:
    """Service for handling AgentConfig business logic and fallback mechanisms."""

    @staticmethod
    def get_agent_config(name: str) -> AgentConfig:
        """Retrieve agent configuration by name with fallback support."""
        try:
            return AgentConfig.get_config(name)
        except AgentConfigNotFoundError:
            # Fallback to default configuration if specified config is missing
            return AgentConfig(
                name=name,
                provider="experiment",
                model="gpt-4",
                lang="default",
                role="default"
            )
