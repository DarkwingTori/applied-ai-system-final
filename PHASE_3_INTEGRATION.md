# Phase 3: Streamlit UI Integration Guide

## Overview

Phase 3 connects your PawPal+ logic layer (Phase 2) with the Streamlit user interface (app.py). The app now acts as a "bridge" between user interactions and your Python classes.

---

## Key Integration Concepts

### 1. Session State Management

**The Problem:** Streamlit reruns the entire script from top to bottom on every button click, which means objects are recreated and lose their state.

**The Solution:** Use `st.session_state` as persistent storage:

```python
# Initialize once, persist forever
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Owner", available_time_minutes=480)
```

This creates an Owner object in session_state that stays alive across all button clicks and page refreshes.

### 2. UI Actions → Logic Layer Methods

Each button press in the UI now calls a corresponding method from your Phase 2 classes:

| UI Action | Logic Method | Class |
|-----------|--------------|-------|
| Add Pet | `owner.add_pet(pet)` | Owner |
| Add Task | `pet.add_task(task)` | Pet |
| Delete Task | `pet.remove_task(title)` | Pet |
| Generate Schedule | `scheduler.generate_schedule()` | Scheduler |
| Mark Complete | `scheduler.mark_task_complete(title)` | Scheduler |

### 3. Data Flow

```
User Input (Streamlit Form)
    ↓
Convert string → Enum (TaskType, Priority)
    ↓
Create Object (Pet, Task)
    ↓
Call Logic Method (add_pet, add_task, generate_schedule)
    ↓
Update Session State
    ↓
Display Result (st.rerun() refreshes the page)
```

---

## How It Works: Step-by-Step

### Step 1: Initialize Owner in Session State

```python
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Owner", available_time_minutes=480)
```

**Result:** The Owner object persists for the entire session.

### Step 2: Add a Pet

```python
if st.button("Add Pet"):
    new_pet = Pet(name="Mochi", species="dog", age=1)
    st.session_state.owner.add_pet(new_pet)  # ← Logic method called
    st.rerun()  # ← Refresh UI to show new pet
```

**Result:**
- Pet object created and added to owner
- UI updates with new pet in the dropdown
- Data persists across button clicks

### Step 3: Add a Task

```python
if st.button("Add Task"):
    # Convert UI strings to enums
    task_type_enum = TaskType[task_type.upper()]
    priority_enum = Priority[priority.upper()]

    # Create task
    new_task = Task(
        title=task_title,
        task_type=task_type_enum,
        duration_minutes=duration,
        priority=priority_enum,
        time_preference=time_pref
    )

    # Add to pet via logic method
    pet.add_task(new_task)  # ← Automatically sets pet_name
    st.rerun()  # ← Refresh
```

**Result:**
- Task created with proper enum types
- Task.pet_name automatically set by add_task()
- Task displays in task list
- pet.calculate_total_care_time() updates automatically

### Step 4: Generate Schedule

```python
if st.button("Create Schedule"):
    scheduler = Scheduler(owner=st.session_state.owner)
    schedule = scheduler.generate_schedule()  # ← Core algorithm
    st.session_state.schedule = schedule
    st.rerun()
```

**Result:**
- Greedy scheduling algorithm runs
- Returns list of (Task, start_time) tuples
- Schedule displays with formatted table
- Reasoning explains each decision

### Step 5: Mark Task Complete

```python
if st.button("Mark Complete"):
    scheduler.mark_task_complete(task_title)  # ← Updates completed_tasks set
    st.rerun()
```

**Result:**
- Task added to completed_tasks set
- get_remaining_tasks() filters out completed tasks
- UI updates to show progress

---

## Running the App

### Prerequisites

```bash
pip install streamlit
```

### Start the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

### Basic Workflow

1. **Sidebar: Set up owner**
   - Enter owner name
   - Adjust available time (slider)

2. **Sidebar: Add pets**
   - Enter pet name and species
   - Click "Add Pet"

3. **Main area: Add tasks**
   - Select a pet
   - Enter task title, type, duration
   - Set priority and time preference
   - Click "Add Task"

4. **Main area: Generate schedule**
   - Click "Create Schedule"
   - View schedule table
   - Expand "Scheduling Reasoning" to see decisions

5. **Track completion**
   - Select a task from dropdown
   - Click "Mark Complete"

---

## File Structure

```
pawpal-main/
├── pawpal_system.py          ← Phase 2 Logic (Owner, Pet, Task, Scheduler)
├── app.py                     ← Phase 3 UI (Streamlit integration)
├── main.py                    ← Demo script
├── tests/
│   ├── test_pawpal_system.py  ← Phase 1 tests
│   └── test_pawpal.py         ← Phase 2 tests
├── reflection.md              ← Project documentation
└── PHASE_3_INTEGRATION.md     ← This file
```

---

## Key Implementation Details

### Session State Keys

| Key | Type | Purpose |
|-----|------|---------|
| `owner` | Owner | Root object holding all pets |
| `current_pet` | str (pet name) | Currently selected pet for task management |
| `scheduler` | Scheduler | Latest scheduler instance |
| `schedule` | list[tuple] | Current schedule (Task, start_time) |

### Enum Conversion

Streamlit dropdown values are strings. The app converts them to enums:

```python
# String from dropdown: "high"
priority_str = "high"

# Convert to enum
priority_enum = Priority[priority_str.upper()]  # Priority.HIGH
```

### Persistent Data Flow

```
Session Start
    ↓
Load persisted objects from st.session_state
    ↓
Display UI based on current state
    ↓
User clicks button
    ↓
Call logic method (e.g., add_task)
    ↓
Update st.session_state (object modified in memory)
    ↓
st.rerun() triggers script re-execution
    ↓
UI refreshes with updated data
    ↓
Loop back to "Display UI based on current state"
```

---

## Common Patterns

### Pattern 1: Add Item to Collection

```python
if st.button("Add Pet"):
    if validation:
        new_pet = Pet(...)
        st.session_state.owner.add_pet(new_pet)  # ← Logic method
        st.success("✓ Added!")
        st.rerun()
    else:
        st.error("Invalid input")
```

### Pattern 2: Remove Item from Collection

```python
if st.button("Delete"):
    removed = pet.remove_task(task_title)  # ← Logic method returns bool
    if removed:
        st.rerun()
```

### Pattern 3: Display List with Delete Options

```python
for idx, task in enumerate(tasks):
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(f"Task: {task.title}")
    with col2:
        if st.button("Delete"):
            pet.remove_task(task.title)  # ← Logic method
            st.rerun()
```

### Pattern 4: Complex Operation with Results

```python
if st.button("Generate Schedule"):
    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()  # ← Logic method
    st.session_state.schedule = schedule  # ← Store result
    st.rerun()

# Display results
if st.session_state.schedule:
    st.dataframe(schedule_data)
    reasoning = scheduler.get_reasoning()  # ← Display explanation
```

---

## Troubleshooting

### Issue: "Pet not found" error
**Cause:** Pet name mismatch between UI and session_state
**Solution:** Use `owner.get_pet(name)` to retrieve, check for None

### Issue: Tasks disappear after refresh
**Cause:** Pet object recreated instead of using session_state
**Solution:** Always work with `st.session_state.owner` and its methods

### Issue: Schedule doesn't update after adding tasks
**Cause:** Old schedule still stored in session_state
**Solution:** Generate schedule calls `scheduler.clear_schedule()` first

### Issue: Button appears to do nothing
**Cause:** Logic executed but UI not refreshed
**Solution:** Add `st.rerun()` after every state-changing operation

---

## Testing the Integration

### Unit Tests
```bash
pytest tests/test_pawpal.py -v
```
All 28 tests should pass (Phase 1 + Phase 2).

### Manual Testing Workflow

1. **Add pet**: Jordan, 180 min available
2. **Add 3 tasks**: Walk (30m, HIGH), Feed (10m, HIGH), Play (20m, MEDIUM)
3. **Generate schedule**: Should show all 3 tasks
4. **Check reasoning**: Should explain priority ordering
5. **Mark task complete**: Walk should move to remaining
6. **Verify persistence**: Refresh page, data should still be there

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│           Streamlit UI (app.py)                 │
│                                                  │
│  [Owner Setup]  [Pet Manager]  [Task Manager]   │
│  [Schedule Gen] [Task Complete] [Results]       │
└──────────────────────┬──────────────────────────┘
                       │
                  st.session_state
                (persistent memory)
                       │
         ┌─────────────┼─────────────┐
         ↓             ↓             ↓
    ┌─────────┐  ┌──────────┐  ┌──────────────┐
    │  Owner  │  │   Pet    │  │  Scheduler   │
    │ Methods │  │ Methods  │  │   Methods    │
    └─────────┘  └──────────┘  └──────────────┘

    pawpal_system.py (Logic Layer - Phase 2)
```

---

## Next Steps

### Phase 3 Enhancements (Optional)

1. **Persistent Storage**: Save schedules to database or CSV
2. **Analytics**: Show weekly trends of pet care time
3. **Notifications**: Remind user when tasks are due
4. **Multi-day Planning**: Plan across multiple days
5. **Pet Profiles**: Store pet preferences and history

### Phase 4: Polish & Deploy

1. Add error handling and input validation
2. Improve visual design with custom CSS
3. Deploy to Streamlit Cloud
4. Add user authentication
5. Create admin panel for managing multiple households

---

## Summary

Phase 3 successfully bridges the gap between your logic layer and user interface:

✅ **Logic layer** (pawpal_system.py) handles all scheduling and data management
✅ **UI layer** (app.py) handles user interactions and display
✅ **Session state** maintains persistent data across page refreshes
✅ **Data flow** is clear: UI → Convert → Create → Logic Method → Update → Refresh

The app is now fully functional for creating, managing, and scheduling pet care tasks!
