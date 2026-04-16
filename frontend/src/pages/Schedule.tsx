import { useState, FormEvent } from "react";
import { api } from "../api/client";
import type { ScheduleResponse, ScheduledTask } from "../types";
import { ConfidenceBadge } from "../components/ConfidenceBadge";

const TASK_TYPES = ["walk", "feeding", "medication", "enrichment", "grooming"] as const;
const PRIORITIES = ["high", "medium", "low"] as const;
const TIME_PREFS = ["morning", "evening", ""] as const;

const TASK_ICONS: Record<string, string> = {
  walk: "🦮",
  feeding: "🍽️",
  medication: "💊",
  enrichment: "🧩",
  grooming: "✂️",
};

const PRIORITY_COLORS: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-700",
};

interface TaskDraft {
  title: string;
  task_type: string;
  duration_minutes: number;
  priority: string;
  description: string;
  time_preference: string;
}

interface PetDraft {
  name: string;
  species: string;
  age: number;
  energy_level: string;
  tasks: TaskDraft[];
}

function emptyTask(): TaskDraft {
  return { title: "", task_type: "walk", duration_minutes: 30, priority: "medium", description: "", time_preference: "" };
}

function emptyPet(): PetDraft {
  return { name: "", species: "dog", age: 2, energy_level: "medium", tasks: [emptyTask()] };
}

interface TaskTip {
  answer: string;
  confidence: number;
}

export function Schedule() {
  const [ownerName, setOwnerName] = useState("");
  const [availableTime, setAvailableTime] = useState(120);
  const [pets, setPets] = useState<PetDraft[]>([emptyPet()]);
  const [result, setResult] = useState<ScheduleResponse | null>(null);
  const [tips, setTips] = useState<Record<string, TaskTip>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updatePet(i: number, field: keyof PetDraft, value: unknown) {
    setPets((prev) => prev.map((p, idx) => idx === i ? { ...p, [field]: value } : p));
  }

  function updateTask(pi: number, ti: number, field: keyof TaskDraft, value: unknown) {
    setPets((prev) =>
      prev.map((p, idx) =>
        idx === pi
          ? { ...p, tasks: p.tasks.map((t, j) => j === ti ? { ...t, [field]: value } : t) }
          : p
      )
    );
  }

  function addTask(pi: number) {
    setPets((prev) => prev.map((p, idx) => idx === pi ? { ...p, tasks: [...p.tasks, emptyTask()] } : p));
  }

  function removeTask(pi: number, ti: number) {
    setPets((prev) => prev.map((p, idx) => idx === pi ? { ...p, tasks: p.tasks.filter((_, j) => j !== ti) } : p));
  }

  function addPet() {
    setPets((prev) => [...prev, emptyPet()]);
  }

  function removePet(i: number) {
    setPets((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function fetchTip(task: ScheduledTask) {
    if (tips[task.task_type]) return;
    try {
      const res = await api.taskTip(task.task_type);
      setTips((prev) => ({ ...prev, [task.task_type]: { answer: res.answer, confidence: res.confidence } }));
    } catch {
      // silently ignore tip failures
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const payload = {
        owner_name: ownerName || "Owner",
        available_time_minutes: availableTime,
        pets: pets.map((p) => ({
          ...p,
          tasks: p.tasks.map((t) => ({
            ...t,
            time_preference: t.time_preference || null,
            frequency: null,
          })),
        })),
      };
      const res = await api.schedule(payload);
      setResult(res);
      // Pre-fetch tips for unique task types
      const uniqueTypes = [...new Set(res.scheduled_tasks.map((t) => t.task_type))];
      uniqueTypes.forEach((type) => {
        api.taskTip(type).then((r) =>
          setTips((prev) => ({ ...prev, [type]: { answer: r.answer, confidence: r.confidence } }))
        ).catch(() => {});
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate schedule.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-6">
      <h1 className="text-xl font-semibold text-pawpal-text mb-1">Schedule Generator</h1>
      <p className="text-sm text-pawpal-muted mb-6">Add your pets and tasks, then generate an optimized daily schedule with AI-powered tips.</p>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Owner info */}
        <div className="rounded-2xl border border-pawpal-border bg-white p-5 shadow-card">
          <h2 className="text-sm font-semibold text-pawpal-text mb-4">Owner Details</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-pawpal-muted mb-1">Your name</label>
              <input
                type="text"
                value={ownerName}
                onChange={(e) => setOwnerName(e.target.value)}
                placeholder="e.g. Jordan"
                className="w-full rounded-lg border border-pawpal-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-300"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-pawpal-muted mb-1">Available time (minutes)</label>
              <input
                type="number"
                min={10}
                max={480}
                value={availableTime}
                onChange={(e) => setAvailableTime(Number(e.target.value))}
                className="w-full rounded-lg border border-pawpal-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-300"
              />
            </div>
          </div>
        </div>

        {/* Pets */}
        {pets.map((pet, pi) => (
          <div key={pi} className="rounded-2xl border border-pawpal-border bg-white p-5 shadow-card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-pawpal-text">Pet {pi + 1}</h2>
              {pets.length > 1 && (
                <button type="button" onClick={() => removePet(pi)} className="text-xs text-red-500 hover:text-red-700">Remove pet</button>
              )}
            </div>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-xs font-medium text-pawpal-muted mb-1">Name</label>
                <input
                  type="text"
                  value={pet.name}
                  onChange={(e) => updatePet(pi, "name", e.target.value)}
                  placeholder="e.g. Bella"
                  required
                  className="w-full rounded-lg border border-pawpal-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-300"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-pawpal-muted mb-1">Species</label>
                <select
                  value={pet.species}
                  onChange={(e) => updatePet(pi, "species", e.target.value)}
                  className="w-full rounded-lg border border-pawpal-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-300"
                >
                  <option value="dog">Dog</option>
                  <option value="cat">Cat</option>
                  <option value="rabbit">Rabbit</option>
                  <option value="bird">Bird</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-pawpal-muted mb-1">Age (years)</label>
                <input
                  type="number"
                  min={0}
                  max={30}
                  value={pet.age}
                  onChange={(e) => updatePet(pi, "age", Number(e.target.value))}
                  className="w-full rounded-lg border border-pawpal-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-300"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-pawpal-muted mb-1">Energy level</label>
                <select
                  value={pet.energy_level}
                  onChange={(e) => updatePet(pi, "energy_level", e.target.value)}
                  className="w-full rounded-lg border border-pawpal-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-300"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>

            {/* Tasks */}
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-pawpal-muted uppercase tracking-wide">Tasks</h3>
              {pet.tasks.map((task, ti) => (
                <div key={ti} className="rounded-xl border border-pawpal-border bg-pawpal-bg p-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs text-pawpal-muted mb-1">Title</label>
                      <input
                        type="text"
                        value={task.title}
                        onChange={(e) => updateTask(pi, ti, "title", e.target.value)}
                        placeholder="e.g. Morning walk"
                        required
                        className="w-full rounded-lg border border-pawpal-border bg-white px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-brand-300"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-pawpal-muted mb-1">Type</label>
                      <select
                        value={task.task_type}
                        onChange={(e) => updateTask(pi, ti, "task_type", e.target.value)}
                        className="w-full rounded-lg border border-pawpal-border bg-white px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-brand-300"
                      >
                        {TASK_TYPES.map((t) => (
                          <option key={t} value={t}>{TASK_ICONS[t]} {t.charAt(0).toUpperCase() + t.slice(1)}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-pawpal-muted mb-1">Duration (min)</label>
                      <input
                        type="number"
                        min={5}
                        max={240}
                        value={task.duration_minutes}
                        onChange={(e) => updateTask(pi, ti, "duration_minutes", Number(e.target.value))}
                        className="w-full rounded-lg border border-pawpal-border bg-white px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-brand-300"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-pawpal-muted mb-1">Priority</label>
                      <select
                        value={task.priority}
                        onChange={(e) => updateTask(pi, ti, "priority", e.target.value)}
                        className="w-full rounded-lg border border-pawpal-border bg-white px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-brand-300"
                      >
                        {PRIORITIES.map((p) => (
                          <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-pawpal-muted mb-1">Time preference</label>
                      <select
                        value={task.time_preference}
                        onChange={(e) => updateTask(pi, ti, "time_preference", e.target.value)}
                        className="w-full rounded-lg border border-pawpal-border bg-white px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-brand-300"
                      >
                        <option value="">Flexible</option>
                        <option value="morning">Morning</option>
                        <option value="evening">Evening</option>
                      </select>
                    </div>
                    <div className="flex items-end">
                      {pet.tasks.length > 1 && (
                        <button type="button" onClick={() => removeTask(pi, ti)} className="text-xs text-red-400 hover:text-red-600">
                          Remove task
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              <button type="button" onClick={() => addTask(pi)} className="text-xs text-brand-500 hover:text-brand-700 font-medium">
                + Add task
              </button>
            </div>
          </div>
        ))}

        <div className="flex gap-3">
          <button type="button" onClick={addPet} className="rounded-xl border border-brand-200 bg-brand-50 px-4 py-2 text-sm font-medium text-brand-600 hover:bg-brand-100 transition-colors">
            + Add another pet
          </button>
          <button
            type="submit"
            disabled={loading}
            className="rounded-xl bg-brand-500 px-6 py-2 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-50 transition-colors"
          >
            {loading ? "Generating…" : "Generate Schedule"}
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-6 rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="mt-8 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-pawpal-text">Your Schedule</h2>
            <span className="text-sm text-pawpal-muted">{result.total_scheduled_time} min scheduled</span>
          </div>

          {/* Scheduled tasks */}
          <div className="space-y-3">
            {result.scheduled_tasks.map((task, i) => (
              <div key={i} className="rounded-2xl border border-pawpal-border bg-white p-4 shadow-card">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{TASK_ICONS[task.task_type]}</span>
                    <div>
                      <p className="text-sm font-semibold text-pawpal-text">{task.title}</p>
                      <p className="text-xs text-pawpal-muted">{task.pet_name} · {task.start_time} · {task.duration_minutes} min</p>
                    </div>
                  </div>
                  <span className={`text-xs rounded-full px-2.5 py-0.5 font-medium ${PRIORITY_COLORS[task.priority]}`}>
                    {task.priority}
                  </span>
                </div>

                {/* RAG tip for this task type */}
                {tips[task.task_type] && (
                  <div className="mt-3 rounded-xl bg-brand-50 border border-brand-100 px-3 py-2">
                    <p className="text-xs font-medium text-brand-700 mb-1">💡 Advisor Tip</p>
                    <p className="text-xs text-brand-800 leading-relaxed line-clamp-3">
                      {tips[task.task_type].answer.split("\n")[0]}
                    </p>
                    <div className="mt-1.5">
                      <ConfidenceBadge confidence={tips[task.task_type].confidence} />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Reasoning */}
          <details className="rounded-xl border border-pawpal-border bg-white p-4">
            <summary className="cursor-pointer text-sm font-medium text-pawpal-text">Scheduling Reasoning</summary>
            <ul className="mt-3 space-y-1">
              {result.reasoning.map((line, i) => (
                <li key={i} className="text-xs text-pawpal-muted font-mono">{line}</li>
              ))}
            </ul>
          </details>
        </div>
      )}
    </div>
  );
}
