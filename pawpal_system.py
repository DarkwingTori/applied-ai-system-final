"""
PawPal+ Pet Care Management System
Core classes for scheduling pet care tasks
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ===== ENUMS =====

class TaskType(Enum):
    """Types of pet care tasks"""
    WALK = "walk"
    FEEDING = "feeding"
    MEDICATION = "medication"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"


class Priority(Enum):
    """Task priority levels with numeric values for comparison"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3


# ===== DATA CLASSES =====

@dataclass
class Task:
    """Represents a pet care task with scheduling requirements"""
    title: str
    task_type: TaskType
    duration_minutes: int
    priority: Priority
    description: str = ""
    time_preference: Optional[str] = None  # "morning", "evening", or None for flexible
    pet_name: str = ""
    frequency: Optional[str] = None  # None, "daily", or "weekly" for recurring tasks
    next_due_date: Optional[str] = None  # YYYY-MM-DD format for recurring tasks

    def get_priority_score(self) -> int:
        """Return numeric priority value (1-3)"""
        return self.priority.value

    def is_high_priority(self) -> bool:
        """Check if priority is HIGH"""
        return self.priority == Priority.HIGH

    def is_time_flexible(self) -> bool:
        """Check if task has no time preference"""
        return self.time_preference is None

    def matches_type(self, task_type: TaskType) -> bool:
        """Check if task matches a specific type"""
        return self.task_type == task_type

    def __str__(self) -> str:
        """Human-readable task representation"""
        return f"{self.title} ({self.duration_minutes}min, {self.priority.name})"

    def create_next_occurrence(self, completion_date: str = None) -> 'Task':
        """Create next occurrence of recurring task

        Args:
            completion_date: Date task was completed (YYYY-MM-DD format)

        Returns:
            New Task instance for next occurrence, or None if not recurring
        """
        if self.frequency is None:
            return None

        from datetime import datetime, timedelta

        # Use today if no completion date provided
        if completion_date is None:
            completion_date = datetime.now().strftime('%Y-%m-%d')

        completed = datetime.strptime(completion_date, '%Y-%m-%d')

        # Calculate next occurrence
        if self.frequency == "daily":
            next_date = completed + timedelta(days=1)
        elif self.frequency == "weekly":
            next_date = completed + timedelta(weeks=1)
        else:
            return None

        # Create new task instance
        next_task = Task(
            title=self.title,
            task_type=self.task_type,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            description=self.description,
            time_preference=self.time_preference,
            pet_name=self.pet_name,
            frequency=self.frequency,
            next_due_date=next_date.strftime('%Y-%m-%d')
        )

        return next_task


@dataclass
class Pet:
    """Represents a pet with care needs and characteristics"""
    name: str
    species: str
    age: int
    energy_level: str = "medium"  # "low", "medium", or "high"
    special_needs: list[str] = field(default_factory=list)
    tasks: list = field(default_factory=list)  # List of Task objects

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet"""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task_title: str) -> bool:
        """Remove a task by title. Returns True if removed, False if not found."""
        for i, task in enumerate(self.tasks):
            if task.title == task_title:
                self.tasks.pop(i)
                return True
        return False

    def get_tasks(self) -> list:
        """Get all tasks for this pet"""
        return self.tasks.copy()

    def get_tasks_by_priority(self, priority: str) -> list:
        """Filter tasks by priority level (low, medium, high)"""
        priority_map = {
            "low": Priority.LOW,
            "medium": Priority.MEDIUM,
            "high": Priority.HIGH
        }
        if priority.lower() not in priority_map:
            raise ValueError(f"Invalid priority: {priority}. Must be 'low', 'medium', or 'high'")
        target_priority = priority_map[priority.lower()]
        return [task for task in self.tasks if task.priority == target_priority]

    def get_high_priority_tasks(self) -> list:
        """Get only high-priority tasks"""
        return [task for task in self.tasks if task.is_high_priority()]

    def calculate_total_care_time(self) -> int:
        """Sum of all task durations in minutes"""
        return sum(task.duration_minutes for task in self.tasks)


@dataclass
class Owner:
    """Represents the pet owner with time constraints and preferences"""
    name: str
    available_time_minutes: int
    preferences: dict = field(default_factory=dict)
    pets: list = field(default_factory=list)  # List of Pet objects

    def add_pet(self, pet) -> None:
        """Add a pet to this owner's collection"""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """Remove a pet by name. Returns True if removed, False if not found."""
        for i, pet in enumerate(self.pets):
            if pet.name == pet_name:
                self.pets.pop(i)
                return True
        return False

    def get_pet(self, pet_name: str) -> Optional:
        """Retrieve a specific pet by name. Returns None if not found."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_pets(self) -> list:
        """Get all pets owned by this owner"""
        return self.pets.copy()

    def has_time_for_task(self, task_duration: int) -> bool:
        """Check if owner has enough available time for a task"""
        return task_duration <= self.available_time_minutes


@dataclass
class Scheduler:
    """Schedules pet care tasks based on priorities and constraints"""
    owner: 'Owner'
    scheduled_tasks: list = field(default_factory=list)  # List of (Task, start_time) tuples
    completed_tasks: set = field(default_factory=set)  # Set of completed task titles
    total_scheduled_time: int = 0
    reasoning: list[str] = field(default_factory=list)

    def generate_schedule(self) -> list[tuple]:
        """
        Main scheduling algorithm. Generates optimized daily plan.
        Returns list of (Task, start_time) tuples.
        """
        # 1. Clear previous schedule
        self.clear_schedule()

        # 2. Collect all tasks from all owner's pets
        all_tasks = []
        for pet in self.owner.pets:
            all_tasks.extend(pet.get_tasks())

        # Edge case: no tasks
        if not all_tasks:
            self.reasoning.append("No tasks to schedule.")
            return []

        # 3. Prioritize tasks (HIGH → MEDIUM → LOW)
        prioritized_tasks = self._prioritize_tasks(all_tasks)

        # 4. Greedy scheduling starting at 9:00 AM
        current_time = 540  # 9:00 AM in minutes since midnight
        remaining_time = self.owner.available_time_minutes

        self.reasoning.append(
            f"Starting schedule at {self._calculate_start_time(current_time)}"
        )
        self.reasoning.append(
            f"Owner has {remaining_time} minutes available today"
        )

        for task in prioritized_tasks:
            if self._can_fit_task(task, remaining_time):
                # Schedule the task
                start_time_str = self._calculate_start_time(current_time)
                self.scheduled_tasks.append((task, start_time_str))

                # Update tracking
                remaining_time -= task.duration_minutes
                current_time += task.duration_minutes
                self.total_scheduled_time += task.duration_minutes

                # Add reasoning
                self.reasoning.append(
                    f"✓ Scheduled: {task.title} for {task.pet_name} "
                    f"at {start_time_str} ({task.duration_minutes}min, "
                    f"{task.priority.name} priority)"
                )
            else:
                # Task doesn't fit
                self.reasoning.append(
                    f"✗ Skipped: {task.title} for {task.pet_name} "
                    f"({task.duration_minutes}min needed, "
                    f"only {remaining_time}min remaining)"
                )

        self.reasoning.append(
            f"\nTotal scheduled: {self.total_scheduled_time} minutes"
        )
        self.reasoning.append(
            f"Remaining time: {remaining_time} minutes"
        )

        return self.scheduled_tasks

    def get_schedule(self) -> list[tuple]:
        """Return the generated schedule"""
        return self.scheduled_tasks

    def get_reasoning(self) -> list[str]:
        """Return scheduling explanations"""
        return self.reasoning

    def clear_schedule(self) -> None:
        """Reset schedule for new scheduling run"""
        self.scheduled_tasks = []
        self.total_scheduled_time = 0
        self.reasoning = []

    def _prioritize_tasks(self, tasks: list) -> list:
        """Private helper: Sort tasks by priority and constraints"""
        def sort_key(task):
            priority_score = task.get_priority_score()
            time_score = 0 if task.time_preference == "morning" else 1
            duration = task.duration_minutes
            # Negate priority to sort HIGH (3) → MEDIUM (2) → LOW (1)
            return (-priority_score, time_score, duration)

        return sorted(tasks, key=sort_key)

    def _can_fit_task(self, task: Task, remaining_time: int) -> bool:
        """Private helper: Check if task fits in available time"""
        return task.duration_minutes <= remaining_time

    def _calculate_start_time(self, current_time: int) -> str:
        """Private helper: Convert minutes since midnight to readable time (e.g., '9:00 AM')"""
        hours = current_time // 60
        minutes = current_time % 60

        # Convert to 12-hour format
        period = "AM"
        if hours >= 12:
            period = "PM"
            if hours > 12:
                hours -= 12
        elif hours == 0:
            hours = 12

        return f"{hours}:{minutes:02d} {period}"

    def mark_task_complete(self, task_title: str, completion_date: str = None) -> bool:
        """Mark a scheduled task as completed and create next occurrence if recurring

        Args:
            task_title: Title of task to mark complete
            completion_date: Date completed (YYYY-MM-DD), defaults to today

        Returns:
            True if task was found and marked complete, False otherwise
        """
        for task, start_time in self.scheduled_tasks:
            if task.title == task_title:
                self.completed_tasks.add(task_title)
                self.reasoning.append(
                    f"✓ Completed: {task.title} at {start_time}"
                )

                # Handle recurring tasks
                if task.frequency is not None:
                    # Find pet and add next occurrence
                    for pet in self.owner.pets:
                        if pet.name == task.pet_name:
                            next_task = task.create_next_occurrence(completion_date)
                            if next_task:
                                pet.add_task(next_task)
                                self.reasoning.append(
                                    f"  → Created next occurrence: {next_task.next_due_date} ({task.frequency})"
                                )
                            break

                return True
        return False

    def is_task_complete(self, task_title: str) -> bool:
        """Check if a task has been marked as completed."""
        return task_title in self.completed_tasks

    def get_remaining_tasks(self) -> list[tuple]:
        """Get list of scheduled tasks that have not been completed."""
        return [
            (task, time) for task, time in self.scheduled_tasks
            if task.title not in self.completed_tasks
        ]

    def _parse_time_to_minutes(self, time_str: str) -> int:
        """Convert time string '9:00 AM' to minutes since midnight"""
        time_part, period = time_str.split()
        hours, minutes = map(int, time_part.split(':'))

        # Convert to 24-hour format
        if period == 'PM' and hours != 12:
            hours += 12
        elif period == 'AM' and hours == 12:
            hours = 0

        return hours * 60 + minutes

    def sort_by_time(self, schedule: list[tuple] = None) -> list[tuple]:
        """Sort scheduled tasks by start time (earliest first)

        Args:
            schedule: Optional schedule to sort. If None, uses self.scheduled_tasks

        Returns:
            List of (Task, start_time) tuples sorted chronologically
        """
        if schedule is None:
            schedule = self.scheduled_tasks

        return sorted(schedule, key=lambda item: self._parse_time_to_minutes(item[1]))

    def filter_by_pet(self, pet_name: str) -> list[tuple]:
        """Filter scheduled tasks by pet name

        Args:
            pet_name: Name of the pet to filter by

        Returns:
            List of (Task, start_time) tuples for the specified pet
        """
        return [
            (task, time) for task, time in self.scheduled_tasks
            if task.pet_name == pet_name
        ]

    def filter_by_status(self, completed: bool) -> list[tuple]:
        """Filter tasks by completion status

        Args:
            completed: True to get completed tasks, False for incomplete

        Returns:
            List of (Task, start_time) tuples matching the status
        """
        if completed:
            return [
                (task, time) for task, time in self.scheduled_tasks
                if task.title in self.completed_tasks
            ]
        else:
            return self.get_remaining_tasks()

    def detect_conflicts(self) -> list[str]:
        """Detect overlapping tasks in the schedule

        Returns:
            List of conflict warning messages
        """
        conflicts = []

        for i, (task1, time1) in enumerate(self.scheduled_tasks):
            # Calculate end time for task1
            start_minutes1 = self._parse_time_to_minutes(time1)
            end_minutes1 = start_minutes1 + task1.duration_minutes

            for j, (task2, time2) in enumerate(self.scheduled_tasks[i+1:], start=i+1):
                start_minutes2 = self._parse_time_to_minutes(time2)
                end_minutes2 = start_minutes2 + task2.duration_minutes

                # Check for overlap: start1 < end2 AND start2 < end1
                if start_minutes1 < end_minutes2 and start_minutes2 < end_minutes1:
                    conflicts.append(
                        f"⚠ Conflict: '{task1.title}' ({time1}) overlaps with "
                        f"'{task2.title}' ({time2})"
                    )

        return conflicts
