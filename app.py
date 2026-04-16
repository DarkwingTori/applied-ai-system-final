"""
PawPal+ Interactive Pet Care Scheduler
Streamlit UI connected to PawPal+ logic layer
"""

import streamlit as st
from pawpal_system import Owner, Pet, Task, TaskType, Priority, Scheduler

# ===== PAGE CONFIG =====
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

st.title("🐾 PawPal+ Pet Care Scheduler")
st.markdown("**Intelligent daily pet care planning based on priorities and time constraints**")

# ===== SESSION STATE INITIALIZATION =====
# Initialize the Owner object in session_state if it doesn't exist
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Owner", available_time_minutes=480)
    st.session_state.current_pet = None
    st.session_state.scheduler = None
    st.session_state.schedule = None

# ===== SIDEBAR: OWNER SETUP =====
with st.sidebar:
    st.header("Owner Setup")

    # Owner name input with reset functionality
    new_owner_name = st.text_input(
        "Owner name",
        value=st.session_state.owner.name,
        key="owner_name_input",
        help="Changing the name creates a new owner profile"
    )

    # Update owner name if changed - creates new owner to avoid data mixing
    if new_owner_name != st.session_state.owner.name and new_owner_name.strip():
        # Create new owner (fresh start with no pets)
        st.session_state.owner = Owner(
            name=new_owner_name,
            available_time_minutes=st.session_state.owner.available_time_minutes
        )
        st.session_state.current_pet = None
        st.session_state.scheduler = None
        st.session_state.schedule = None
        st.info(f"Created new owner profile for {new_owner_name}")

    # Available time per day
    available_time = st.slider(
        "Available time per day (minutes)",
        min_value=30,
        max_value=480,
        value=st.session_state.owner.available_time_minutes,
        step=15,
        key="available_time_input"
    )

    if available_time != st.session_state.owner.available_time_minutes:
        st.session_state.owner.available_time_minutes = available_time

    st.divider()

    # Pet management
    st.subheader("Pets")

    # Get list of pet names
    pet_names = [pet.name for pet in st.session_state.owner.get_all_pets()]

    if pet_names:
        st.session_state.current_pet = st.selectbox(
            "Select pet to manage tasks",
            pet_names,
            key="pet_selector"
        )
    else:
        st.info("No pets yet. Add one below!")
        st.session_state.current_pet = None

    st.divider()

    # Add new pet
    st.subheader("Add New Pet")
    col1, col2 = st.columns(2)
    with col1:
        new_pet_name = st.text_input("Pet name", value="")
    with col2:
        new_pet_species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])

    if st.button("Add Pet", key="add_pet_btn"):
        if new_pet_name.strip():
            # Check if pet already exists
            if st.session_state.owner.get_pet(new_pet_name) is None:
                new_pet = Pet(name=new_pet_name, species=new_pet_species, age=1)
                st.session_state.owner.add_pet(new_pet)
                st.session_state.current_pet = new_pet_name
                st.success(f"✓ Added {new_pet_name} the {new_pet_species}!")
                st.rerun()
            else:
                st.error(f"Pet '{new_pet_name}' already exists!")
        else:
            st.error("Please enter a pet name")

# ===== MAIN CONTENT =====
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Pet Care Tasks")

    if st.session_state.current_pet:
        pet = st.session_state.owner.get_pet(st.session_state.current_pet)

        # Add task section
        st.subheader(f"Add task for {pet.name}")

        col_task_a, col_task_b, col_task_c = st.columns(3)

        with col_task_a:
            task_title = st.text_input("Task title", value="", key="task_title_input")

        with col_task_b:
            task_type = st.selectbox(
                "Task type",
                ["walk", "feeding", "medication", "enrichment", "grooming"],
                key="task_type_input"
            )

        with col_task_c:
            duration = st.number_input(
                "Duration (min)",
                min_value=1,
                max_value=240,
                value=15,
                key="task_duration_input"
            )

        col_priority_a, col_priority_b = st.columns(2)

        with col_priority_a:
            priority = st.selectbox(
                "Priority",
                ["low", "medium", "high"],
                index=2,
                key="task_priority_input"
            )

        with col_priority_b:
            time_preference = st.selectbox(
                "Time preference",
                ["flexible", "morning", "evening"],
                key="task_time_pref_input"
            )

        if st.button("Add Task", key="add_task_btn", use_container_width=True):
            if task_title.strip():
                # Convert string inputs to enums
                task_type_enum = TaskType[task_type.upper()]
                priority_enum = Priority[priority.upper()]
                time_pref = None if time_preference == "flexible" else time_preference

                # Create and add task
                new_task = Task(
                    title=task_title,
                    task_type=task_type_enum,
                    duration_minutes=int(duration),
                    priority=priority_enum,
                    time_preference=time_pref
                )
                pet.add_task(new_task)
                st.success(f"✓ Added task: {task_title}")
                st.rerun()
            else:
                st.error("Please enter a task title")

        st.divider()

        # Display tasks for current pet
        st.subheader(f"Tasks for {pet.name}")
        tasks = pet.get_tasks()

        if tasks:
            # Create task display with delete option
            for idx, task in enumerate(tasks):
                col_task_display, col_task_delete = st.columns([4, 1])

                with col_task_display:
                    priority_colors = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
                    priority_icon = priority_colors.get(task.priority.name, "")
                    time_pref_str = f" | ⏰ {task.time_preference}" if task.time_preference else ""
                    recurring_str = f" | 🔄 {task.frequency}" if task.frequency else ""

                    st.write(
                        f"{priority_icon} **{task.title}** ({task.duration_minutes}min) "
                        f"| {task.task_type.value}{time_pref_str}{recurring_str}"
                    )

                with col_task_delete:
                    if st.button("✕", key=f"delete_task_{idx}"):
                        pet.remove_task(task.title)
                        st.rerun()

            total_time = pet.calculate_total_care_time()
            st.info(f"Total care time: **{total_time} minutes**")
        else:
            st.info(f"No tasks for {pet.name} yet. Add one above!")

    else:
        st.info("👈 Add a pet in the sidebar first!")

with col2:
    st.header("Owner Info")

    st.metric("Name", st.session_state.owner.name)
    st.metric("Available time", f"{st.session_state.owner.available_time_minutes} min/day")
    st.metric("Number of pets", len(st.session_state.owner.get_all_pets()))

    # Calculate total care time needed
    total_needed = 0
    for pet in st.session_state.owner.get_all_pets():
        total_needed += pet.calculate_total_care_time()

    st.metric("Total care time needed", f"{total_needed} min")

    # Time comparison
    st.divider()
    available = st.session_state.owner.available_time_minutes
    if total_needed > 0:
        utilization = (total_needed / available) * 100 if available > 0 else 0
        st.metric("Time utilization", f"{utilization:.1f}%")

        if total_needed <= available:
            st.success("✓ All tasks fit in available time!")
        else:
            st.warning(f"⚠ {total_needed - available} minutes over limit")

# ===== SCHEDULE GENERATION =====
st.divider()
st.header("Generate Daily Schedule")

if st.button("📋 Create Schedule", use_container_width=True, key="generate_schedule_btn"):
    # Check if there are tasks
    total_tasks = sum(len(pet.get_tasks()) for pet in st.session_state.owner.get_all_pets())

    if total_tasks == 0:
        st.error("Please add at least one task before generating a schedule.")
    else:
        # Create scheduler and generate schedule
        st.session_state.scheduler = Scheduler(owner=st.session_state.owner)
        st.session_state.schedule = st.session_state.scheduler.generate_schedule()

        st.success("✓ Schedule generated successfully!")
        st.rerun()

# ===== DISPLAY SCHEDULE =====
if st.session_state.schedule is not None and len(st.session_state.schedule) > 0:
    st.subheader("Your Daily Schedule")

    # Phase 4: Add sorting and filtering controls
    col_control_a, col_control_b = st.columns(2)

    with col_control_a:
        sort_by_time = st.checkbox("Sort chronologically", value=True, key="sort_checkbox")

    with col_control_b:
        pet_names_for_filter = ["All pets"] + [pet.name for pet in st.session_state.owner.get_all_pets()]
        filter_pet = st.selectbox(
            "Filter by pet",
            pet_names_for_filter,
            key="filter_pet_select"
        )

    # Apply sorting and filtering
    schedule_to_display = st.session_state.schedule

    if sort_by_time:
        schedule_to_display = st.session_state.scheduler.sort_by_time(schedule_to_display)

    if filter_pet != "All pets":
        schedule_to_display = st.session_state.scheduler.filter_by_pet(filter_pet)

    # Display schedule as table
    schedule_data = []
    for task, start_time in schedule_to_display:
        schedule_data.append({
            "Time": start_time,
            "Task": task.title,
            "Pet": task.pet_name,
            "Duration": f"{task.duration_minutes} min",
            "Priority": task.priority.name
        })

    st.dataframe(schedule_data, use_container_width=True)

    # Phase 4: Conflict detection
    conflicts = st.session_state.scheduler.detect_conflicts()
    if conflicts:
        st.warning("⚠️ Schedule Conflicts Detected")
        for conflict in conflicts:
            st.write(conflict)

    # Display reasoning in expander
    with st.expander("📝 Scheduling Reasoning", expanded=False):
        reasoning = st.session_state.scheduler.get_reasoning()
        for reason in reasoning:
            st.write(reason)

    # Task completion tracking
    st.subheader("Task Completion")

    col_complete_a, col_complete_b = st.columns([3, 1])

    with col_complete_a:
        incomplete_tasks = st.session_state.scheduler.get_remaining_tasks()
        if incomplete_tasks:
            task_titles = [task.title for task, _ in incomplete_tasks]
            selected_task = st.selectbox("Mark task as complete:", task_titles, key="complete_task_select")

            if st.button("✓ Mark Complete", key="mark_complete_btn"):
                st.session_state.scheduler.mark_task_complete(selected_task)
                st.success(f"✓ Marked '{selected_task}' as complete!")
                st.rerun()

    with col_complete_b:
        remaining = len(st.session_state.scheduler.get_remaining_tasks())
        st.metric("Tasks remaining", remaining)

    # Schedule summary
    st.divider()
    col_summary_a, col_summary_b, col_summary_c = st.columns(3)

    with col_summary_a:
        st.metric("Scheduled", len(st.session_state.schedule))

    with col_summary_b:
        st.metric("Total time", f"{st.session_state.scheduler.total_scheduled_time} min")

    with col_summary_c:
        remaining_time = st.session_state.owner.available_time_minutes - st.session_state.scheduler.total_scheduled_time
        st.metric("Remaining time", f"{remaining_time} min")

elif st.session_state.schedule is not None and len(st.session_state.schedule) == 0:
    st.warning("⚠️ No tasks could be scheduled. Check your available time and task durations.")

st.divider()
st.caption("PawPal+ Phase 3: Streamlit UI Integration with PawPal+ Logic Layer")
