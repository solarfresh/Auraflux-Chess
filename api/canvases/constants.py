from django.db import models
from django.utils.translation import gettext_lazy as _


class NodeType(models.TextChoices):
    EVENT = 'EVENT', _('Event')
    OUTCOME = 'OUTCOME', _('Outcome')
    BOUNDARY = 'BOUNDARY', _('Boundary')
    ENTITY = 'ENTITY', _('Entity')
    FOCUS = 'FOCUS', _('Focus')
    RESOURCE = 'RESOURCE', _('Resource')
    CONCEPT = 'CONCEPT', _('Concept')
    INSIGHT = 'INSIGHT', _('Insight')
    QUERY = 'QUERY', _('Query')
    NAVIGATION = 'NAVIGATION', _('Navigation')
    GROUP = 'GROUP', _('Group')


class HandleType(models.TextChoices):
    SOURCE = 'source', _('Source')
    TARGET = 'target', _('Target')


class HandlePosition(models.TextChoices):
    TOP = 'top', _('Top')
    BOTTOM = 'bottom', _('Bottom')
    LEFT = 'left', _('Left')
    RIGHT = 'right', _('Right')


class EdgeType(models.TextChoices):
    VALIDATES = 'VALIDATES', _('Validates')
    CONSTRAINS = 'CONSTRAINS', _('Constrains')
    TRIGGERS = 'TRIGGERS', _('Triggers')
    REF = 'REF', _('Ref')
    LINK = 'LINK', _('Link')
