from core.constants import EntityStatus
from core.models import BaseModel
from django.db import models

from .constants import EdgeType, NodeType


class Canvas(BaseModel):
    title = models.CharField(max_length=255)

class Node(BaseModel):
    canvas = models.ForeignKey(Canvas, on_delete=models.CASCADE, related_name='nodes', db_index=True)
    label = models.CharField(max_length=255)
    node_type = models.CharField(max_length=20, choices=NodeType.choices, default=NodeType.CONCEPT)
    content = models.TextField(blank=True, null=True)
    pos_x = models.FloatField()
    pos_y = models.FloatField()
    status = models.CharField(max_length=20, choices=EntityStatus.choices, default=EntityStatus.ACTIVE)
    rationale = models.TextField(blank=True, null=True)

class Edge(BaseModel):
    canvas = models.ForeignKey(Canvas, on_delete=models.CASCADE, related_name='edges', db_index=True)
    source = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='outgoing_edges')
    target = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='incoming_edges')
    label = models.CharField(max_length=255, blank=True, null=True)
    edge_type = models.CharField(max_length=20, choices=EdgeType.choices, default=EdgeType.LINK)
    weight = models.FloatField(default=1.0)
    status = models.CharField(max_length=20, choices=EntityStatus.choices)
    evidence = models.TextField(blank=True, null=True)
    rationale = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    source_handle = models.CharField(max_length=255, blank=True, null=True)
    target_handle = models.CharField(max_length=255, blank=True, null=True)
