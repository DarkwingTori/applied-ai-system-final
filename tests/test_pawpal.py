"""
Comprehensive tests for PawPal+ Phase 2 implementation
Tests scheduling logic, task management, and edge cases
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pawpal_system import Owner, Pet, Task, TaskType, Priority, Scheduler


# ===== CATEGORY 1: TASK COMPLETION (2 tests) =====

def test_mark_task_complete():
    """Test marking a task as completed"""
    owner = Owner(name="Jordan", available_time_minutes=100)
    pet = Pet(name="Mochi", species="dog", age=3)
    task = Task(
        title="Walk",
        task_type=TaskType.WALK,
        duration_minutes=30,
        priority=Priority.HIGH
    )
    pet.add_task(task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    scheduler.generate_schedule()

    # Mark task complete
    result = scheduler.mark_task_complete("Walk")
    assert result is True
    assert scheduler.is_task_complete("Walk") is True

    # Try to mark non-existent task
    result = scheduler.mark_task_complete("NonExistent")
    assert result is False


def test_get_remaining_tasks():
    """Test getting remaining (incomplete) tasks"""
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

    # All tasks remaining initially
    assert len(scheduler.get_remaining_tasks()) == 2

    # Mark one complete
    scheduler.mark_task_complete("Walk")
    remaining = scheduler.get_remaining_tasks()
    assert len(remaining) == 1
    assert remaining[0][0].title == "Feed"


# ===== CATEGORY 2: TASK ADDITION (2 tests) =====

def test_add_task_increases_count():
    """Test that adding a task increases the pet's task count"""
    pet = Pet(name="Luna", species="cat", age=5)
    assert len(pet.get_tasks()) == 0

    task = Task(
        title="Feed",
        task_type=TaskType.FEEDING,
        duration_minutes=10,
        priority=Priority.HIGH
    )
    pet.add_task(task)
    assert len(pet.get_tasks()) == 1

    task2 = Task(
        title="Play",
        task_type=TaskType.ENRICHMENT,
        duration_minutes=15,
        priority=Priority.MEDIUM
    )
    pet.add_task(task2)
    assert len(pet.get_tasks()) == 2


def test_add_task_sets_pet_name():
    """Test that adding a task automatically sets the pet_name"""
    pet = Pet(name="Mochi", species="dog", age=3)
    task = Task(
        title="Walk",
        task_type=TaskType.WALK,
        duration_minutes=30,
        priority=Priority.HIGH
    )

    # Before adding, pet_name should be empty
    assert task.pet_name == ""

    # After adding, pet_name should be set to pet's name
    pet.add_task(task)
    assert task.pet_name == "Mochi"


# ===== CATEGORY 3: SCHEDULING ALGORITHM (4 tests) =====

def test_schedule_prioritizes_high_tasks():
    """Test that HIGH priority tasks are scheduled before MEDIUM/LOW"""
    owner = Owner(name="Jordan", available_time_minutes=200)
    pet = Pet(name="Mochi", species="dog", age=3)

    high_task = Task(
        title="Medication",
        task_type=TaskType.MEDICATION,
        duration_minutes=5,
        priority=Priority.HIGH
    )
    low_task = Task(
        title="Grooming",
        task_type=TaskType.GROOMING,
        duration_minutes=30,
        priority=Priority.LOW
    )
    medium_task = Task(
        title="Play",
        task_type=TaskType.ENRICHMENT,
        duration_minutes=20,
        priority=Priority.MEDIUM
    )

    pet.add_task(low_task)
    pet.add_task(high_task)
    pet.add_task(medium_task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()

    # HIGH should come first
    assert schedule[0][0].title == "Medication"
    assert schedule[1][0].title == "Play"
    assert schedule[2][0].title == "Grooming"


def test_schedule_respects_time_limit():
    """Test that scheduler doesn't exceed available time"""
    owner = Owner(name="Jordan", available_time_minutes=50)
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
        duration_minutes=15,
        priority=Priority.HIGH
    )
    task3 = Task(
        title="Play",
        task_type=TaskType.ENRICHMENT,
        duration_minutes=20,
        priority=Priority.MEDIUM
    )

    pet.add_task(task1)
    pet.add_task(task2)
    pet.add_task(task3)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()

    # Only first two tasks should fit (30 + 15 = 45 minutes)
    assert len(schedule) == 2
    assert scheduler.total_scheduled_time == 45
    assert scheduler.total_scheduled_time <= owner.available_time_minutes


def test_schedule_with_time_preferences():
    """Test that morning tasks are prioritized"""
    owner = Owner(name="Jordan", available_time_minutes=200)
    pet = Pet(name="Luna", species="cat", age=5)

    morning_task = Task(
        title="Medication",
        task_type=TaskType.MEDICATION,
        duration_minutes=5,
        priority=Priority.MEDIUM,
        time_preference="morning"
    )
    flexible_task = Task(
        title="Play",
        task_type=TaskType.ENRICHMENT,
        duration_minutes=10,
        priority=Priority.MEDIUM,
        time_preference=None
    )

    pet.add_task(flexible_task)
    pet.add_task(morning_task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()

    # Morning task should come first (same priority, but morning preference)
    assert schedule[0][0].title == "Medication"
    assert schedule[1][0].title == "Play"


def test_schedule_with_multiple_pets():
    """Test scheduling with multiple pets and their tasks"""
    owner = Owner(name="Jordan", available_time_minutes=200)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)

    # Add tasks to Mochi
    mochi.add_task(Task(
        title="Walk",
        task_type=TaskType.WALK,
        duration_minutes=30,
        priority=Priority.HIGH
    ))
    mochi.add_task(Task(
        title="Feed Mochi",
        task_type=TaskType.FEEDING,
        duration_minutes=10,
        priority=Priority.HIGH
    ))

    # Add tasks to Luna
    luna.add_task(Task(
        title="Feed Luna",
        task_type=TaskType.FEEDING,
        duration_minutes=10,
        priority=Priority.HIGH
    ))
    luna.add_task(Task(
        title="Play",
        task_type=TaskType.ENRICHMENT,
        duration_minutes=20,
        priority=Priority.MEDIUM
    ))

    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()

    # Should have all 4 tasks scheduled
    assert len(schedule) == 4

    # Extract pet names from schedule
    scheduled_pet_names = {task.pet_name for task, _ in schedule}
    assert "Mochi" in scheduled_pet_names
    assert "Luna" in scheduled_pet_names


# ===== CATEGORY 4: EDGE CASES (7 tests) =====

def test_schedule_with_no_tasks():
    """Test scheduling when there are no tasks"""
    owner = Owner(name="Jordan", available_time_minutes=100)
    pet = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()

    assert len(schedule) == 0
    assert "No tasks to schedule." in scheduler.get_reasoning()


def test_schedule_with_no_pets():
    """Test scheduling when owner has no pets"""
    owner = Owner(name="Jordan", available_time_minutes=100)

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()

    assert len(schedule) == 0


def test_schedule_with_zero_time():
    """Test scheduling when owner has no available time"""
    owner = Owner(name="Jordan", available_time_minutes=0)
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task(
        title="Walk",
        task_type=TaskType.WALK,
        duration_minutes=30,
        priority=Priority.HIGH
    ))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()

    # No tasks should be scheduled
    assert len(schedule) == 0


def test_task_removal():
    """Test removing tasks from a pet"""
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
    assert len(pet.get_tasks()) == 2

    # Remove first task
    result = pet.remove_task("Walk")
    assert result is True
    assert len(pet.get_tasks()) == 1
    assert pet.get_tasks()[0].title == "Feed"

    # Try to remove non-existent task
    result = pet.remove_task("NonExistent")
    assert result is False


def test_get_tasks_by_priority():
    """Test filtering tasks by priority level"""
    pet = Pet(name="Luna", species="cat", age=5)

    pet.add_task(Task(
        title="Medication",
        task_type=TaskType.MEDICATION,
        duration_minutes=5,
        priority=Priority.HIGH
    ))
    pet.add_task(Task(
        title="Feed",
        task_type=TaskType.FEEDING,
        duration_minutes=10,
        priority=Priority.HIGH
    ))
    pet.add_task(Task(
        title="Play",
        task_type=TaskType.ENRICHMENT,
        duration_minutes=15,
        priority=Priority.MEDIUM
    ))
    pet.add_task(Task(
        title="Grooming",
        task_type=TaskType.GROOMING,
        duration_minutes=20,
        priority=Priority.LOW
    ))

    # Test filtering by each priority
    high_tasks = pet.get_tasks_by_priority("high")
    assert len(high_tasks) == 2
    assert all(t.priority == Priority.HIGH for t in high_tasks)

    medium_tasks = pet.get_tasks_by_priority("medium")
    assert len(medium_tasks) == 1
    assert medium_tasks[0].priority == Priority.MEDIUM

    low_tasks = pet.get_tasks_by_priority("low")
    assert len(low_tasks) == 1
    assert low_tasks[0].priority == Priority.LOW


def test_calculate_total_care_time():
    """Test calculating total care time for a pet"""
    pet = Pet(name="Mochi", species="dog", age=3)

    pet.add_task(Task(
        title="Walk",
        task_type=TaskType.WALK,
        duration_minutes=30,
        priority=Priority.HIGH
    ))
    pet.add_task(Task(
        title="Feed",
        task_type=TaskType.FEEDING,
        duration_minutes=10,
        priority=Priority.HIGH
    ))
    pet.add_task(Task(
        title="Play",
        task_type=TaskType.ENRICHMENT,
        duration_minutes=20,
        priority=Priority.MEDIUM
    ))

    total = pet.calculate_total_care_time()
    assert total == 60


def test_invalid_priority_string():
    """Test error handling for invalid priority strings"""
    pet = Pet(name="Luna", species="cat", age=5)

    with pytest.raises(ValueError):
        pet.get_tasks_by_priority("invalid")

    with pytest.raises(ValueError):
        pet.get_tasks_by_priority("urgent")


# ===== CATEGORY 5: OWNER METHODS (3 tests) =====

def test_owner_add_remove_pet():
    """Test adding and removing pets from owner"""
    owner = Owner(name="Jordan", available_time_minutes=100)

    pet1 = Pet(name="Mochi", species="dog", age=3)
    pet2 = Pet(name="Luna", species="cat", age=5)

    owner.add_pet(pet1)
    owner.add_pet(pet2)
    assert len(owner.get_all_pets()) == 2

    # Remove pet
    result = owner.remove_pet("Mochi")
    assert result is True
    assert len(owner.get_all_pets()) == 1
    assert owner.get_all_pets()[0].name == "Luna"

    # Try to remove non-existent pet
    result = owner.remove_pet("NonExistent")
    assert result is False


def test_owner_get_pet():
    """Test retrieving a specific pet from owner"""
    owner = Owner(name="Jordan", available_time_minutes=100)

    pet1 = Pet(name="Mochi", species="dog", age=3)
    pet2 = Pet(name="Luna", species="cat", age=5)

    owner.add_pet(pet1)
    owner.add_pet(pet2)

    # Get existing pet
    retrieved_pet = owner.get_pet("Mochi")
    assert retrieved_pet is not None
    assert retrieved_pet.name == "Mochi"
    assert retrieved_pet.species == "dog"

    # Try to get non-existent pet
    retrieved_pet = owner.get_pet("NonExistent")
    assert retrieved_pet is None


def test_owner_has_time_for_task():
    """Test checking if owner has time for a task"""
    owner = Owner(name="Jordan", available_time_minutes=100)

    # Tasks that fit
    assert owner.has_time_for_task(50) is True
    assert owner.has_time_for_task(100) is True

    # Tasks that don't fit
    assert owner.has_time_for_task(101) is False
    assert owner.has_time_for_task(200) is False
