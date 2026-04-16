"""
Phase 4 Tests: Smart Algorithms
Tests for sorting, filtering, recurring tasks, and conflict detection
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from pawpal_system import Owner, Pet, Task, TaskType, Priority, Scheduler


def test_sort_by_time():
    """Test sorting scheduled tasks by start time"""
    owner = Owner(name="Jordan", available_time_minutes=200)
    pet = Pet(name="Mochi", species="dog", age=3)

    # Add tasks that will be scheduled in specific order
    pet.add_task(Task(
        title="Evening walk",
        task_type=TaskType.WALK,
        duration_minutes=30,
        priority=Priority.HIGH
    ))
    pet.add_task(Task(
        title="Morning walk",
        task_type=TaskType.WALK,
        duration_minutes=30,
        priority=Priority.HIGH,
        time_preference="morning"
    ))

    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    scheduler.generate_schedule()

    # Sort by time
    sorted_schedule = scheduler.sort_by_time()

    # First task should be earliest in time
    # Morning preference should come first due to prioritization
    assert sorted_schedule[0][0].title == "Morning walk"
    assert sorted_schedule[1][0].title == "Evening walk"


def test_filter_by_pet():
    """Test filtering scheduled tasks by pet name"""
    owner = Owner(name="Jordan", available_time_minutes=200)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)

    mochi.add_task(Task(
        title="Walk Mochi",
        task_type=TaskType.WALK,
        duration_minutes=30,
        priority=Priority.HIGH
    ))
    luna.add_task(Task(
        title="Feed Luna",
        task_type=TaskType.FEEDING,
        duration_minutes=10,
        priority=Priority.HIGH
    ))

    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler(owner=owner)
    scheduler.generate_schedule()

    # Filter by pet
    mochi_tasks = scheduler.filter_by_pet("Mochi")
    assert len(mochi_tasks) == 1
    assert mochi_tasks[0][0].title == "Walk Mochi"

    luna_tasks = scheduler.filter_by_pet("Luna")
    assert len(luna_tasks) == 1
    assert luna_tasks[0][0].title == "Feed Luna"


def test_filter_by_status():
    """Test filtering tasks by completion status"""
    owner = Owner(name="Jordan", available_time_minutes=100)
    pet = Pet(name="Mochi", species="dog", age=3)

    task1 = Task(
        title="Walk",
        task_type=TaskType.WALK,
        duration_minutes=30,
        priority=Priority.HIGH
    )
    task2 = Task(
        title="Feed",
        task_type=TaskType.FEEDING,
        duration_minutes=10,
        priority=Priority.HIGH
    )

    pet.add_task(task1)
    pet.add_task(task2)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    scheduler.generate_schedule()

    # Initially, all tasks are incomplete
    incomplete = scheduler.filter_by_status(completed=False)
    assert len(incomplete) == 2

    completed_tasks = scheduler.filter_by_status(completed=True)
    assert len(completed_tasks) == 0

    # Mark one complete
    scheduler.mark_task_complete("Walk")

    # Now one complete, one incomplete
    incomplete = scheduler.filter_by_status(completed=False)
    assert len(incomplete) == 1
    assert incomplete[0][0].title == "Feed"

    completed_tasks = scheduler.filter_by_status(completed=True)
    assert len(completed_tasks) == 1
    assert completed_tasks[0][0].title == "Walk"


def test_recurring_task_creation():
    """Test creating next occurrence of recurring task"""
    task = Task(
        title="Daily feeding",
        task_type=TaskType.FEEDING,
        duration_minutes=10,
        priority=Priority.HIGH,
        frequency="daily"
    )

    # Create next occurrence
    today = "2026-02-09"
    next_task = task.create_next_occurrence(completion_date=today)

    assert next_task is not None
    assert next_task.title == "Daily feeding"
    assert next_task.frequency == "daily"
    assert next_task.next_due_date == "2026-02-10"  # Next day

    # Test weekly recurrence
    weekly_task = Task(
        title="Weekly grooming",
        task_type=TaskType.GROOMING,
        duration_minutes=30,
        priority=Priority.MEDIUM,
        frequency="weekly"
    )

    next_weekly = weekly_task.create_next_occurrence(completion_date=today)
    assert next_weekly.next_due_date == "2026-02-16"  # 7 days later

    # Test non-recurring task
    normal_task = Task(
        title="One-time walk",
        task_type=TaskType.WALK,
        duration_minutes=20,
        priority=Priority.HIGH
    )

    next_normal = normal_task.create_next_occurrence()
    assert next_normal is None


def test_mark_complete_creates_recurrence():
    """Test that marking recurring task complete auto-creates next occurrence"""
    owner = Owner(name="Jordan", available_time_minutes=100)
    pet = Pet(name="Mochi", species="dog", age=3)

    # Create recurring task
    recurring_task = Task(
        title="Daily feeding",
        task_type=TaskType.FEEDING,
        duration_minutes=10,
        priority=Priority.HIGH,
        frequency="daily"
    )

    pet.add_task(recurring_task)
    owner.add_pet(pet)

    # Initial task count
    assert len(pet.get_tasks()) == 1

    # Generate schedule and mark complete
    scheduler = Scheduler(owner=owner)
    scheduler.generate_schedule()
    scheduler.mark_task_complete("Daily feeding", completion_date="2026-02-09")

    # New task should be auto-created
    assert len(pet.get_tasks()) == 2

    # Find the new task
    tasks = pet.get_tasks()
    new_task = [t for t in tasks if t.next_due_date is not None][0]
    assert new_task.next_due_date == "2026-02-10"
    assert new_task.frequency == "daily"


def test_detect_conflicts():
    """Test conflict detection for overlapping tasks"""
    owner = Owner(name="Jordan", available_time_minutes=200)
    pet = Pet(name="Mochi", species="dog", age=3)

    # Create tasks that will overlap (both HIGH priority, will be scheduled back-to-back)
    # But we'll manually create overlapping schedule for testing
    task1 = Task(
        title="Walk",
        task_type=TaskType.WALK,
        duration_minutes=60,
        priority=Priority.HIGH
    )
    task2 = Task(
        title="Feed",
        task_type=TaskType.FEEDING,
        duration_minutes=30,
        priority=Priority.HIGH
    )

    pet.add_task(task1)
    pet.add_task(task2)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    scheduler.generate_schedule()

    # Normal schedule shouldn't have conflicts (tasks are back-to-back)
    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 0  # No overlaps in greedy algorithm

    # Manually create overlapping schedule to test conflict detection
    scheduler.scheduled_tasks = [
        (task1, "9:00 AM"),  # 9:00 AM - 10:00 AM
        (task2, "9:30 AM")   # 9:30 AM - 10:00 AM (overlaps!)
    ]

    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1
    assert "Conflict" in conflicts[0]
    assert "Walk" in conflicts[0]
    assert "Feed" in conflicts[0]


def test_no_conflicts_when_tasks_adjacent():
    """Test that adjacent tasks (no gap) don't trigger conflicts"""
    owner = Owner(name="Jordan", available_time_minutes=100)
    pet = Pet(name="Mochi", species="dog", age=3)

    task1 = Task(
        title="Walk",
        task_type=TaskType.WALK,
        duration_minutes=30,
        priority=Priority.HIGH
    )
    task2 = Task(
        title="Feed",
        task_type=TaskType.FEEDING,
        duration_minutes=10,
        priority=Priority.HIGH
    )

    pet.add_task(task1)
    pet.add_task(task2)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    scheduler.generate_schedule()

    # Tasks scheduled back-to-back should have no conflicts
    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 0
