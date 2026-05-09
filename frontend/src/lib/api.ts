import axios from "axios";

export const api = axios.create({
  baseURL: "/api",
  timeout: 5000
});

export async function createBurst(count: number, durationMs: number) {
  const response = await api.post(`/jobs/burst?count=${count}&duration_ms=${durationMs}`);
  return response.data;
}

export async function createJob(jobType: string, priority: string, durationMs: number) {
  const response = await api.post("/jobs", {
    job_type: jobType,
    priority,
    duration_ms: durationMs,
    failure_rate: 0.08
  });
  return response.data;
}
