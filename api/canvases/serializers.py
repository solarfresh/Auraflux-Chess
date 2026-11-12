from rest_framework import serializers

from .models import Canvas, Edge, Node


class BatchNodePositionUpdateSerializer(serializers.Serializer):
    nodes = serializers.ListField(
        child=serializers.DictField()
    )

    def validate_nodes(self, value):
        for node in value:
            if 'id' not in node or 'position' not in node:
                raise serializers.ValidationError("Each node must have 'id' and 'position'.")
            if 'x' not in node['position'] or 'y' not in node['position']:
                raise serializers.ValidationError("Position must contain 'x' and 'y'.")
            try:
                float(node['position']['x'])
                float(node['position']['y'])
            except (ValueError, TypeError):
                raise serializers.ValidationError("Position 'x' and 'y' must be numbers.")
        return value

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
