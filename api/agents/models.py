from core.models import BaseModel
from django.db import models

from .exceptions import AgentConfigNotFoundError


class AgentConfig(BaseModel):
    """Agent Configuration Model for persisting AI agent settings."""
    name = models.CharField(max_length=100, unique=True)
    provider = models.CharField(max_length=50)
    model = models.CharField(max_length=100)
    lang = models.CharField(max_length=50, default='default')
    role = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.provider}/{self.model})"

    @classmethod
    def get_config(cls, name):
        """Retrieve AgentConfig by name, raising AgentConfigNotFoundError if missing."""
        try:
            return cls.objects.get(name=name)
        except cls.DoesNotExist:
            raise AgentConfigNotFoundError(name)
