import uuid
from unittest.mock import MagicMock

import pytest
from core.utils import (create_serialized_data, get_serialized_data_by_id,
                        update_serialized_data_by_id)
from rest_framework.exceptions import ValidationError


def test_get_serialized_data_by_id_success(mock_model_instance, mock_model_manager_factory):
    model_class = MagicMock()
    model_manager = mock_model_manager_factory(instance=mock_model_instance)
    model_manager.get = MagicMock(return_value=mock_model_instance)
    model_class.objects = model_manager

    serializer_class = MagicMock()
    serializer_instance = MagicMock()
    serializer_instance.data = {"id": 1, "name": "test"}
    serializer_class.return_value = serializer_instance

    test_id = uuid.uuid4()
    result = get_serialized_data_by_id(
        id=test_id,
        model_class=model_class,
        serializer_class=serializer_class
    )

    assert result == {"id": 1, "name": "test"}
    model_class.objects.get.assert_called_once_with(id=test_id)


def test_get_serialized_data_by_id_not_found(mock_model_manager_factory):
    model_class = MagicMock()
    model_class.objects = mock_model_manager_factory(raise_does_not_exist=True)
    model_class.DoesNotExist = Exception

    serializer_class = MagicMock()

    test_id = uuid.uuid4()
    with pytest.raises(Exception):
        get_serialized_data_by_id(
            id=test_id,
            model_class=model_class,
            serializer_class=serializer_class
        )


def test_update_serialized_data_by_id_success(mock_model_instance, mock_model_manager_factory):
    model_class = MagicMock()
    model_class.objects = mock_model_manager_factory(instance=mock_model_instance)
    mock_model_instance.__class__.objects = model_class.objects

    serializer_class = MagicMock()
    serializer_instance = MagicMock()
    serializer_instance.is_valid.return_value = True
    serializer_instance.data = {"id": 1, "name": "updated"}
    serializer_class.return_value = serializer_instance

    test_id = uuid.uuid4()
    result = update_serialized_data_by_id(
        id=test_id,
        data={"name": "updated"},
        model_class=model_class,
        serializer_class=serializer_class
    )

    assert result == {"id": 1, "name": "updated"}
    serializer_instance.save.assert_called_once()

def test_update_serialized_data_by_id_validation_error(mock_model_instance, mock_model_manager_factory):
    model_class = MagicMock()
    model_class.objects = mock_model_manager_factory(instance=mock_model_instance)
    mock_model_instance.__class__.objects = model_class.objects

    serializer_class = MagicMock()
    serializer_instance = MagicMock()
    serializer_instance.is_valid.return_value = False
    serializer_instance.errors = {"name": ["Invalid"]}
    serializer_class.return_value = serializer_instance

    test_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        update_serialized_data_by_id(
            id=test_id,
            data={"name": "invalid"},
            model_class=model_class,
            serializer_class=serializer_class
        )

def test_update_serialized_data_by_id_not_found(mock_model_manager_factory):
    model_class = MagicMock()
    model_class.objects = mock_model_manager_factory(raise_does_not_exist=True)
    model_class.DoesNotExist = Exception

    serializer_class = MagicMock()

    test_id = uuid.uuid4()
    with pytest.raises(Exception):
        update_serialized_data_by_id(
            id=test_id,
            data={"name": "test"},
            model_class=model_class,
            serializer_class=serializer_class
        )

def test_create_serialized_data_success():
    serializer_class = MagicMock()
    serializer_instance = MagicMock()
    serializer_instance.is_valid.return_value = True
    serializer_instance.save.return_value = MagicMock()

    response_serializer_instance = MagicMock()
    response_serializer_instance.data = {"id": 1, "name": "test"}

    def side_effect(*args, **kwargs):
        if "data" in kwargs or len(args) > 0 and isinstance(args[0], dict):
            return serializer_instance
        return response_serializer_instance

    serializer_class.side_effect = side_effect

    data = {"name": "test"}
    result = create_serialized_data(
        data=data,
        serializer_class=serializer_class
    )

    assert result == {"id": 1, "name": "test"}
    serializer_instance.save.assert_called_once()

def test_create_serialized_data_validation_error():
    serializer_class = MagicMock()
    serializer_instance = MagicMock()
    serializer_instance.is_valid.return_value = False
    serializer_instance.errors = {"name": ["Required"]}
    serializer_class.return_value = serializer_instance

    with pytest.raises(ValidationError):
        create_serialized_data(
            data={},
            serializer_class=serializer_class
        )
    serializer_instance.save.assert_not_called()
