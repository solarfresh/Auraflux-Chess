from rest_framework import serializers

from .models import Canvas, Edge, Node


class NodeSerializer(serializers.ModelSerializer):
    position = serializers.SerializerMethodField()
    type = serializers.CharField(source='node_type')

    class Meta:
        model = Node
        fields = ['id', 'label', 'type', 'content', 'position', 'status', 'rationale']

    def get_position(self, obj):
        return {'x': obj.pos_x, 'y': obj.pos_y}

class EdgeSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='edge_type')

    class Meta:
        model = Edge
        fields = ['id', 'source', 'target', 'label', 'type', 'weight', 'status', 'evidence', 'rationale']

class CanvasGraphSerializer(serializers.ModelSerializer):
    nodes = NodeSerializer(many=True, read_only=True)
    edges = EdgeSerializer(many=True, read_only=True)
    canvasId = serializers.UUIDField(source='id')

    class Meta:
        model = Canvas
        fields = ['canvasId', 'nodes', 'edges']
