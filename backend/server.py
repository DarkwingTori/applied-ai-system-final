"""
PawPal+ FastAPI Server
Exposes RAG advisor and scheduling endpoints for the React frontend.
"""

import sys
import os
from pathlib import Path

# Allow importing pawpal_system from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.rag_engine import ask, get_task_tip
from pawpal_system import Owner, Pet, Task, TaskType, Priority, Scheduler

app = FastAPI(title="PawPal+ AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
        "http://localhost:5175", "http://127.0.0.1:5175",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────

class AskRequest(BaseModel):
    query: str
    pet_name: str = ""
    task_type: str = ""


class AskResponse(BaseModel):
    answer: str
    confidence: float
    sources: list[str]
    low_confidence: bool


class TaskTipRequest(BaseModel):
    task_type: str


class ScheduleTaskIn(BaseModel):
    title: str
    task_type: str          # "walk" | "feeding" | "medication" | "enrichment" | "grooming"
    duration_minutes: int
    priority: str           # "low" | "medium" | "high"
    description: str = ""
    time_preference: str | None = None
    frequency: str | None = None


class PetIn(BaseModel):
    name: str
    species: str
    age: int
    energy_level: str = "medium"
    tasks: list[ScheduleTaskIn] = []


class ScheduleRequest(BaseModel):
    owner_name: str
    available_time_minutes: int
    pets: list[PetIn]


class ScheduledTaskOut(BaseModel):
    title: str
    task_type: str
    duration_minutes: int
    priority: str
    pet_name: str
    start_time: str
    completed: bool


class ScheduleResponse(BaseModel):
    scheduled_tasks: list[ScheduledTaskOut]
    reasoning: list[str]
    total_scheduled_time: int


# ── Helpers ───────────────────────────────────────────────────────────────────

_TASK_TYPE_MAP = {
    "walk": TaskType.WALK,
    "feeding": TaskType.FEEDING,
    "medication": TaskType.MEDICATION,
    "enrichment": TaskType.ENRICHMENT,
    "grooming": TaskType.GROOMING,
}

_PRIORITY_MAP = {
    "low": Priority.LOW,
    "medium": Priority.MEDIUM,
    "high": Priority.HIGH,
}


def _build_task(t: ScheduleTaskIn) -> Task:
    task_type = _TASK_TYPE_MAP.get(t.task_type.lower())
    if not task_type:
        raise HTTPException(status_code=422, detail=f"Unknown task_type: {t.task_type}")
    priority = _PRIORITY_MAP.get(t.priority.lower())
    if not priority:
        raise HTTPException(status_code=422, detail=f"Unknown priority: {t.priority}")
    return Task(
        title=t.title,
        task_type=task_type,
        duration_minutes=t.duration_minutes,
        priority=priority,
        description=t.description,
        time_preference=t.time_preference,
        frequency=t.frequency,
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/ask", response_model=AskResponse)
def ask_advisor(req: AskRequest):
    """RAG-powered pet care question answering."""
    if not req.query.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")
    try:
        result = ask(req.query, pet_name=req.pet_name, task_type=req.task_type)
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG pipeline error: {e}")
    return AskResponse(**result)


@app.post("/api/task-tip", response_model=AskResponse)
def task_tip(req: TaskTipRequest):
    """Return a RAG-grounded tip for a specific task type (walk, feeding, etc.)."""
    try:
        result = get_task_tip(req.task_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return AskResponse(**result)


@app.post("/api/schedule", response_model=ScheduleResponse)
def generate_schedule(req: ScheduleRequest):
    """Run the PawPal+ greedy scheduling algorithm and return the plan."""
    owner = Owner(
        name=req.owner_name,
        available_time_minutes=req.available_time_minutes,
    )
    for pet_data in req.pets:
        pet = Pet(
            name=pet_data.name,
            species=pet_data.species,
            age=pet_data.age,
            energy_level=pet_data.energy_level,
        )
        for task_data in pet_data.tasks:
            pet.add_task(_build_task(task_data))
        owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    scheduled = scheduler.generate_schedule()

    tasks_out = [
        ScheduledTaskOut(
            title=task.title,
            task_type=task.task_type.value,
            duration_minutes=task.duration_minutes,
            priority=task.priority.name.lower(),
            pet_name=task.pet_name,
            start_time=start_time,
            completed=scheduler.is_task_complete(task.title),
        )
        for task, start_time in scheduled
    ]

    return ScheduleResponse(
        scheduled_tasks=tasks_out,
        reasoning=scheduler.get_reasoning(),
        total_scheduled_time=scheduler.total_scheduled_time,
    )
