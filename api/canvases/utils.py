from rest_framework.exceptions import ValidationError


def update_node_positions_by_serializer(data, canvas, model_class, serializer_class):
    serializer = serializer_class(data=data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)

    nodes_data = serializer.validated_data['nodes']
    node_ids = [n['id'] for n in nodes_data]
    nodes = list(model_class.objects.filter(id__in=node_ids, canvas=canvas))
    if len(nodes) != len(nodes_data):
        return None

    node_map = {str(n.id): n for n in nodes}
    for n_data in nodes_data:
        node = node_map[str(n_data['id'])]
        node.pos_x = float(n_data['position']['x'])
        node.pos_y = float(n_data['position']['y'])

    model_class.objects.bulk_update(nodes, ['pos_x', 'pos_y'])
    return len(nodes)
