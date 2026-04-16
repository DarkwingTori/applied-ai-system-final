import type { AskResponse, ScheduleResponse } from "../types";

const BASE_URL = "http://localhost:8000";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json();
}

export const api = {
  ask(query: string, petName?: string, taskType?: string): Promise<AskResponse> {
    return post("/api/ask", {
      query,
      pet_name: petName ?? "",
      task_type: taskType ?? "",
    });
  },

  taskTip(taskType: string): Promise<AskResponse> {
    return post("/api/task-tip", { task_type: taskType });
  },

  schedule(payload: {
    owner_name: string;
    available_time_minutes: number;
    pets: {
      name: string;
      species: string;
      age: number;
      energy_level: string;
      tasks: {
        title: string;
        task_type: string;
        duration_minutes: number;
        priority: string;
        description?: string;
        time_preference?: string | null;
        frequency?: string | null;
      }[];
    }[];
  }): Promise<ScheduleResponse> {
    return post("/api/schedule", payload);
  },
};
