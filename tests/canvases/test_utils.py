import pytest
from canvases.models import Canvas, Node
from canvases.serializers import BatchNodePositionUpdateSerializer
from canvases.utils import update_node_positions_by_serializer
from rest_framework.exceptions import ValidationError


@pytest.mark.django_db
def test_update_node_positions_by_serializer_success(canvas):
    node = Node.objects.create(canvas=canvas, pos_x=0.0, pos_y=0.0)
    data = {
        "nodes": [
            {
                "id": node.id,
                "position": {"x": 150.5, "y": 250.75}
            }
        ]
    }

    updated_count = update_node_positions_by_serializer(
        data=data,
        canvas=canvas,
        model_class=Node,
        serializer_class=BatchNodePositionUpdateSerializer
    )

    assert updated_count == 1
    node.refresh_from_db()
    assert node.pos_x == 150.5
    assert node.pos_y == 250.75

@pytest.mark.django_db
def test_update_node_positions_by_serializer_validation_error(canvas):
    data = {
        "nodes": [
            {
                "position": {"x": "invalid", "y": 200.0}
            }
        ]
    }

    with pytest.raises(ValidationError):
        update_node_positions_by_serializer(
            data=data,
            canvas=canvas,
            model_class=Node,
            serializer_class=BatchNodePositionUpdateSerializer
        )

@pytest.mark.django_db
def test_update_node_positions_by_serializer_node_mismatch_or_not_found(canvas):
    other_canvas = Canvas.objects.create(title="Other Canvas")
    other_node = Node.objects.create(canvas=other_canvas, pos_x=0.0, pos_y=0.0)

    data = {
        "nodes": [
            {
                "id": other_node.id,
                "position": {"x": 100.0, "y": 100.0}
            }
        ]
    }

    result = update_node_positions_by_serializer(
        data=data,
        canvas=canvas,
        model_class=Node,
        serializer_class=BatchNodePositionUpdateSerializer
    )

    assert result is None
    other_node.refresh_from_db()
    assert other_node.pos_x == 0.0
    assert other_node.pos_y == 0.0
