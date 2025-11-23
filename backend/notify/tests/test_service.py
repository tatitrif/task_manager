
from unittest.mock import patch, MagicMock
import pytest
from django.contrib.auth import get_user_model
from tasks.models import ListTask, Task, TaskStatus
from accounts.models import Profile
from tasks.serializers import TaskSerializer

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create(username="testuser", password="testpassword")


@pytest.fixture
def another_user():
    return User.objects.create(username="anotheruser", password="testpassword")


@pytest.fixture
def list_task(user):
    return ListTask.objects.create(name="Test List", owner=user)


@pytest.mark.django_db
@patch('notify.service.send_telegram_message')
@patch('notify.service.ws_send_user')
@patch('notify.service.is_online')
def test_notify_task_change_created(mock_is_online, mock_ws_send_user, mock_send_telegram_message, list_task, user, another_user):
    from notify.service import notify_task_change
    mock_is_online.return_value = True

    task = Task(name="New Task", list_tasks=list_task, assigned_to=another_user)
    notify_task_change(task, "created")

    # The owner and the new assignee both receive a 'task_updated' event.
    # The new assignee also receives a 'task_notify' event.
    # Total calls = 1 (owner) + 2 (assignee) = 3.
    assert mock_ws_send_user.call_count == 3
    mock_send_telegram_message.assert_not_called()

    # Check call for task owner
    mock_ws_send_user.assert_any_call(
        user.id,
        {
            "type": "task_updated",
            "action": "created",
            "task": TaskSerializer(task).data,
        },
    )

    # Check call for assigned user
    mock_ws_send_user.assert_any_call(
        another_user.id,
        {
            "type": "task_updated",
            "action": "created",
            "task": TaskSerializer(task).data,
        },
    )


@pytest.mark.django_db
@patch('notify.service.send_telegram_message')
@patch('notify.service.ws_send_user')
@patch('notify.service.is_online')
def test_notify_task_change_updated(mock_is_online, mock_ws_send_user, mock_send_telegram_message, list_task, user, another_user):
    from notify.service import notify_task_change
    mock_is_online.return_value = False
    Profile.objects.create(user=user, telegram_id=12345)
    Profile.objects.create(user=another_user, telegram_id=54321)

    task = Task(name="Updated Task", list_tasks=list_task, assigned_to=another_user)
    notify_task_change(task, "updated", old_assigned_to_id=user.id)

    assert mock_ws_send_user.call_count == 0
    assert mock_send_telegram_message.call_count == 2
