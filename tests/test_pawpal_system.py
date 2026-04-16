"""
Unit tests for PawPal+ system classes
Tests class instantiation and basic relationships
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path to import pawpal_system
sys.path.insert(0, str(Path(__file__).parent.parent))

from pawpal_system import Owner, Pet, Task, TaskType, Priority, Scheduler


def test_owner_creation():
    """Test Owner instantiation with valid data"""
    owner = Owner(name="Jordan", available_time_minutes=480, preferences={}, pets=[])
    assert owner.name == "Jordan"
    assert owner.available_time_minutes == 480
    assert owner.preferences == {}
    assert owner.pets == []


def test_pet_creation():
    """Test Pet instantiation with valid data"""
    pet = Pet(name="Mochi", species="dog", age=3)
    assert pet.name == "Mochi"
    assert pet.species == "dog"
    assert pet.age == 3
    assert pet.energy_level == "medium"  # Default value
    assert pet.special_needs == []  # Default empty list
    assert pet.tasks == []  # Default empty list


def test_task_creation():
    """Test Task instantiation with enums"""
    task = Task(
        title="Morning walk",
        task_type=TaskType.WALK,
        duration_minutes=30,
        priority=Priority.HIGH
    )
    assert task.title == "Morning walk"
    assert task.task_type == TaskType.WALK
    assert task.duration_minutes == 30
    assert task.priority == Priority.HIGH
    assert task.description == ""  # Default value
    assert task.time_preference is None  # Default value
    assert task.pet_name == ""  # Default value


def test_task_priority_comparison():
    """Test Task priority enum values are comparable"""
    high_task = Task(
        title="Medication",
        task_type=TaskType.MEDICATION,
        duration_minutes=5,
        priority=Priority.HIGH
    )
    low_task = Task(
        title="Grooming",
        task_type=TaskType.GROOMING,
        duration_minutes=45,
        priority=Priority.LOW
    )

    # Test priority score method
    assert high_task.get_priority_score() == 3
    assert low_task.get_priority_score() == 1
    assert high_task.get_priority_score() > low_task.get_priority_score()

    # Test is_high_priority method
    assert high_task.is_high_priority() is True
    assert low_task.is_high_priority() is False


def test_task_time_flexibility():
    """Test Task time flexibility checks"""
    flexible_task = Task(
        title="Playtime",
        task_type=TaskType.ENRICHMENT,
        duration_minutes=20,
        priority=Priority.MEDIUM,
        time_preference=None
    )
    morning_task = Task(
        title="Breakfast",
        task_type=TaskType.FEEDING,
        duration_minutes=15,
        priority=Priority.HIGH,
        time_preference="morning"
    )

    assert flexible_task.is_time_flexible() is True
    assert morning_task.is_time_flexible() is False


def test_task_type_matching():
    """Test Task type matching"""
    walk_task = Task(
        title="Evening walk",
        task_type=TaskType.WALK,
        duration_minutes=30,
        priority=Priority.MEDIUM
    )

    assert walk_task.matches_type(TaskType.WALK) is True
    assert walk_task.matches_type(TaskType.FEEDING) is False


def test_task_string_representation():
    """Test Task __str__ method"""
    task = Task(
        title="Medication",
        task_type=TaskType.MEDICATION,
        duration_minutes=5,
        priority=Priority.HIGH
    )

    expected = "Medication (5min, HIGH)"
    assert str(task) == expected


def test_scheduler_initialization():
    """Test Scheduler can be created with an Owner"""
    owner = Owner(name="Jordan", available_time_minutes=480)
    scheduler = Scheduler(owner=owner)

    assert scheduler.owner == owner
    assert scheduler.scheduled_tasks == []
    assert scheduler.total_scheduled_time == 0
    assert scheduler.reasoning == []


def test_enum_values():
    """Test enum values are correctly defined"""
    # TaskType enum
    assert TaskType.WALK.value == "walk"
    assert TaskType.FEEDING.value == "feeding"
    assert TaskType.MEDICATION.value == "medication"
    assert TaskType.ENRICHMENT.value == "enrichment"
    assert TaskType.GROOMING.value == "grooming"

    # Priority enum
    assert Priority.LOW.value == 1
    assert Priority.MEDIUM.value == 2
    assert Priority.HIGH.value == 3


def test_mutable_defaults_not_shared():
    """Test that mutable default values are not shared between instances"""
    pet1 = Pet(name="Mochi", species="dog", age=3)
    pet2 = Pet(name="Luna", species="cat", age=2)

    # Add task to pet1
    task1 = Task(
        title="Walk Mochi",
        task_type=TaskType.WALK,
        duration_minutes=30,
        priority=Priority.HIGH
    )
    pet1.tasks.append(task1)

    # pet2 should have empty task list (not shared)
    assert len(pet1.tasks) == 1
    assert len(pet2.tasks) == 0

    # Test same for Owner
    owner1 = Owner(name="Jordan", available_time_minutes=480)
    owner2 = Owner(name="Alex", available_time_minutes=360)

    owner1.pets.append(pet1)
    assert len(owner1.pets) == 1
    assert len(owner2.pets) == 0
