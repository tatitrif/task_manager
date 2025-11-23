
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from tasks.models import ListTask, Task, TaskStatus

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(username="testuser", password="testpassword")


@pytest.fixture
def another_user():
    return User.objects.create_user(username="anotheruser", password="testpassword")


@pytest.fixture
def list_task(user):
    return ListTask.objects.create(name="Test List", owner=user)


@pytest.mark.django_db
class TestListTaskModel:
    def test_list_task_creation(self, user):
        list_task = ListTask.objects.create(name="My Test List", owner=user)
        assert list_task.name == "My Test List"
        assert list_task.owner == user
        assert str(list_task) == "My Test List"

    def test_list_task_ordering(self, user):
        list_task1 = ListTask.objects.create(name="List 1", owner=user)
        list_task2 = ListTask.objects.create(name="List 2", owner=user)
        assert list(ListTask.objects.all()) == [list_task2, list_task1]


@pytest.mark.django_db
@patch('notify.signals.notify_task_change')
class TestTaskModel:
    def test_task_creation(self, mock_notify, list_task, user):
        task = Task.objects.create(
            name="Test Task",
            list_tasks=list_task,
            assigned_to=user,
        )
        assert task.name == "Test Task"
        assert task.list_tasks == list_task
        assert task.status == TaskStatus.IN_PROGRESS
        assert str(task) == "Test Task"
        mock_notify.assert_called()

    def test_task_save_method(self, mock_notify, list_task, user, another_user):
        task = Task.objects.create(name="Task 1", list_tasks=list_task)
        assert task.status == TaskStatus.PENDING

        task.assigned_to = user
        task.save()
        assert task.status == TaskStatus.IN_PROGRESS

        task.assigned_to = another_user
        task.save()
        assert task.status == TaskStatus.IN_PROGRESS
        assert mock_notify.call_count > 1

    def test_mark_completed(self, mock_notify, list_task, user):
        task = Task.objects.create(
            name="Completable Task",
            list_tasks=list_task,
            assigned_to=user,
        )
        assert task.mark_completed() is True
        assert task.status == TaskStatus.COMPLETED
        assert task.is_completed is True

        # Try to complete it again
        assert task.mark_completed() is False
        assert mock_notify.call_count > 1

    def test_mark_overdue(self, mock_notify, list_task, user):
        yesterday = timezone.now() - timedelta(days=1)
        task = Task.objects.create(
            name="Overdue Task",
            list_tasks=list_task,
            assigned_to=user,
            complete_before=yesterday,
        )
        assert task.mark_overdue() is True
        assert task.status == TaskStatus.OVERDUE

        # Try to mark it overdue again
        assert task.mark_overdue() is False

        # Should not mark as overdue if already completed
        task.status = TaskStatus.COMPLETED
        task.save()
        assert task.mark_overdue() is False
        assert mock_notify.call_count > 1

    def test_is_completed_property(self, mock_notify, list_task, user):
        task = Task.objects.create(
            name="Property Task",
            list_tasks=list_task,
            assigned_to=user,
        )
        assert task.is_completed is False
        task.status = TaskStatus.COMPLETED
        task.save()
        assert task.is_completed is True
        mock_notify.assert_called()
