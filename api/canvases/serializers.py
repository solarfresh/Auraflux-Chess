from rest_framework import serializers
from django.db import transaction

from .constants import HandlePosition, HandleType
from .models import Canvas, Edge, Node, NodeHandle


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


class NodeHandleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeHandle
        fields = ['id', 'handle_type', 'position']


class NodeSerializer(serializers.ModelSerializer):
    position = serializers.SerializerMethodField()
    type = serializers.CharField(source='node_type')
    handles = NodeHandleSerializer(many=True, read_only=True)

    class Meta:
        model = Node
        fields = ['id', 'label', 'type', 'content', 'position', 'status', 'rationale', 'handles']

    def get_position(self, obj):
        return {'x': obj.pos_x, 'y': obj.pos_y}


class NodeCreateSerializer(serializers.ModelSerializer):
    position = serializers.DictField(write_only=True)
    temp_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)

    class Meta:
        model = Node
        fields = ['label', 'node_type', 'position', 'temp_id']

    def create(self, validated_data):
        position = validated_data.pop('position')
        validated_data.pop('temp_id', None)
        validated_data['pos_x'] = position['x']
        validated_data['pos_y'] = position['y']
        node = super().create(validated_data)
        for handle_type in HandleType:
            for position in HandlePosition:
                NodeHandle.objects.create(
                    node=node,
                    handle_type=handle_type,
                    position=position
                )

        return node


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
    source = serializers.CharField()
    target = serializers.CharField()
    sourceHandle = serializers.CharField(source='source_handle', required=False, allow_blank=True, allow_null=True)
    targetHandle = serializers.CharField(source='target_handle', required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Edge
        fields = ['source', 'target', 'edge_type', 'weight', 'label', 'evidence', 'rationale', 'metadata', 'sourceHandle', 'targetHandle']

    def validate(self, data):
        # We don't need to look up in database here because nodes are created in the same transaction
        # and IDs are not yet assigned.
        # Just ensure 'source' and 'target' are strings (temp_ids).
        if not isinstance(data.get('source'), str) or not isinstance(data.get('target'), str):
            raise serializers.ValidationError("Source and target must be string references (temp_ids).")
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


class BatchDeleteNodeSerializer(serializers.Serializer):
    def delete_nodes(self, canvas_id):
        from .models import Edge, Node
        nodes_to_delete = Node.objects.filter(canvas_id=canvas_id, status='REVIEW')
        node_ids = list(nodes_to_delete.values_list('id', flat=True))

        edges_to_delete = Edge.objects.filter(source__in=node_ids) | Edge.objects.filter(target__in=node_ids)
        edge_ids = list(edges_to_delete.values_list('id', flat=True))

        edges_to_delete.delete()
        nodes_to_delete.delete()

        return node_ids, edge_ids


class CanvasGraphImportSerializer(serializers.Serializer):
    canvas_id = serializers.UUIDField()
    nodes = NodeCreateSerializer(many=True)
    edges = EdgeCreateSerializer(many=True, required=False, default=list)

    def _get_canvas(self, canvas_id):
        try:
            return Canvas.objects.get(id=canvas_id)
        except Canvas.DoesNotExist:
            raise serializers.ValidationError(f"Canvas {canvas_id} not found.")

    def _create_nodes(self, canvas, nodes_data):
        created_nodes_map = {}
        nodes_to_create = []
        temp_ids = []

        for index, n_data in enumerate(nodes_data):
            temp_id = n_data.pop('temp_id', None) or str(index)
            temp_ids.append(temp_id)

            position = n_data.pop('position')
            n_data['pos_x'] = position['x']
            n_data['pos_y'] = position['y']
            nodes_to_create.append(Node(canvas=canvas, **n_data))

        persisted_nodes = Node.objects.bulk_create(nodes_to_create)

        handles_to_create = []
        for node in persisted_nodes:
            for handle_type in HandleType:
                for position in HandlePosition:
                    handles_to_create.append(
                        NodeHandle(
                            node=node,
                            handle_type=handle_type,
                            position=position
                        )
                    )
        NodeHandle.objects.bulk_create(handles_to_create)

        for temp_id, node in zip(temp_ids, persisted_nodes):
            created_nodes_map[str(temp_id)] = node

        return created_nodes_map, persisted_nodes

    def _create_edges(self, canvas, edges_data, created_nodes_map):
        edges_to_create = []
        for e_data in edges_data:
            source_temp = str(e_data.get('source'))
            target_temp = str(e_data.get('target'))

            if source_temp not in created_nodes_map or target_temp not in created_nodes_map:
                raise serializers.ValidationError("Edge source or target reference not found in created nodes.")

            source_node = created_nodes_map[source_temp]
            target_node = created_nodes_map[target_temp]

            if source_node.canvas_id != canvas.id or target_node.canvas_id != canvas.id:
                raise serializers.ValidationError("Edge source or target does not belong to the target canvas.")

            e_data['canvas'] = canvas
            e_data['source'] = source_node
            e_data['target'] = target_node

            edges_to_create.append(Edge(**e_data))

        return Edge.objects.bulk_create(edges_to_create)

    def create(self, validated_data):
        canvas = self._get_canvas(validated_data['canvas_id'])
        nodes_data = validated_data['nodes']
        edges_data = validated_data.get('edges', [])

        with transaction.atomic():
            created_nodes_map, persisted_nodes = self._create_nodes(canvas, nodes_data)
            persisted_edges = self._create_edges(canvas, edges_data, created_nodes_map)

        return {
            "canvas": canvas,
            "persisted_nodes": persisted_nodes,
            "persisted_edges": persisted_edges
        }
