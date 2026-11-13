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


class NodeCreateSerializer(serializers.ModelSerializer):
    position = serializers.DictField(write_only=True)

    class Meta:
        model = Node
        fields = ['label', 'node_type', 'position']

    def create(self, validated_data):
        position = validated_data.pop('position')
        validated_data['pos_x'] = position['x']
        validated_data['pos_y'] = position['y']
        return super().create(validated_data)


class NodeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ['label', 'content', 'status', 'rationale']
        extra_kwargs = {
            'label': {'required': False, 'allow_blank': False, 'max_length': 255},
            'content': {'required': False, 'allow_blank': True, 'allow_null': True},
            'status': {'required': False, 'allow_blank': False, 'max_length': 20},
            'rationale': {'required': False, 'allow_blank': True, 'allow_null': True},
        }


class EdgeCreateSerializer(serializers.ModelSerializer):
    sourceHandle = serializers.CharField(source='source_handle', required=False, allow_blank=True, allow_null=True)
    targetHandle = serializers.CharField(source='target_handle', required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Edge
        fields = ['source', 'target', 'edge_type', 'weight', 'label', 'evidence', 'rationale', 'metadata', 'sourceHandle', 'targetHandle']

    def validate(self, data):
        canvas_id = self.context.get('canvas_id')
        if not canvas_id:
            raise serializers.ValidationError("Canvas ID is required.")

        source = data.get('source')
        target = data.get('target')

        if not Node.objects.filter(id=source.id, canvas_id=canvas_id).exists():
            raise serializers.ValidationError(f"Source node {source.id} does not exist in canvas {canvas_id}.")

        if not Node.objects.filter(id=target.id, canvas_id=canvas_id).exists():
            raise serializers.ValidationError(f"Target node {target.id} does not exist in canvas {canvas_id}.")

        return data


class EdgeSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='edge_type')
    sourceHandle = serializers.CharField(source='source_handle', allow_blank=True, allow_null=True)
    targetHandle = serializers.CharField(source='target_handle', allow_blank=True, allow_null=True)

    class Meta:
        model = Edge
        fields = ['id', 'source', 'target', 'label', 'type', 'weight', 'status', 'evidence', 'rationale', 'metadata', 'sourceHandle', 'targetHandle']


class EdgeUpdateSerializer(serializers.ModelSerializer):
    sourceHandle = serializers.CharField(source='source_handle', required=False, allow_blank=True, allow_null=True)
    targetHandle = serializers.CharField(source='target_handle', required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Edge
        fields = ['label', 'weight', 'status', 'evidence', 'rationale', 'metadata', 'sourceHandle', 'targetHandle']
        extra_kwargs = {
            'label': {'required': False, 'allow_blank': True, 'allow_null': True, 'max_length': 255},
            'weight': {'required': False},
            'status': {'required': False, 'allow_blank': False, 'max_length': 20},
            'evidence': {'required': False, 'allow_blank': True, 'allow_null': True},
            'rationale': {'required': False, 'allow_blank': True, 'allow_null': True},
            'metadata': {'required': False},
        }


class CanvasGraphSerializer(serializers.ModelSerializer):
    nodes = NodeSerializer(many=True, read_only=True)
    edges = EdgeSerializer(many=True, read_only=True)

    class Meta:
        model = Canvas
        fields = ['id', 'title', 'nodes', 'edges']
