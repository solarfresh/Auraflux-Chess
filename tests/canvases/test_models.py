import pytest
from canvases.models import Canvas, Node, NodeHandle


@pytest.mark.django_db
def test_node_handle_relationship():
    canvas = Canvas.objects.create(title="Test Canvas")
    node = Node.objects.create(canvas=canvas, label="Node 1", pos_x=0, pos_y=0)

    # Access via node.handles (related_name)
    handle1 = NodeHandle.objects.create(node=node, handle_type="source", position="top")
    handle2 = NodeHandle.objects.create(node=node, handle_type="target", position="bottom")

    # Static analysis tools (like Pylance) may not detect 'handles' due to dynamic Django nature.
    # It works at runtime.
    assert node.handles.count() == 2
    assert handle1 in node.handles.all()
    assert handle2 in node.handles.all()

@pytest.mark.django_db
def test_node_handle_cascade_delete():
    canvas = Canvas.objects.create(title="Test Canvas")
    node = Node.objects.create(canvas=canvas, label="Node 1", pos_x=0, pos_y=0)
    NodeHandle.objects.create(node=node, handle_type="source", position="top")

    assert NodeHandle.objects.count() == 1
    node.delete()
    assert NodeHandle.objects.count() == 0
