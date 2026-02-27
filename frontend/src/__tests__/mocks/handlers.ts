/** MSW request handlers for API mocking. */

import { http, HttpResponse } from "msw";
import { makeMatches, makePreferences } from "./data";

const API = "/api";

export const handlers = [
  http.get(`${API}/jobs`, () => {
    const matches = makeMatches(5);
    const jobs = matches.map((m) => m.job);
    return HttpResponse.json({ items: jobs, total: 5, limit: 20, offset: 0 });
  }),

  http.get(`${API}/matches`, () => {
    return HttpResponse.json({
      items: makeMatches(5),
      total: 5,
      limit: 20,
      offset: 0,
    });
  }),

  http.get(`${API}/matches/:id`, ({ params }) => {
    const matches = makeMatches(5);
    const match = matches.find((m) => m.id === Number(params.id));
    if (!match) return HttpResponse.json({ detail: "Not found" }, { status: 404 });
    return HttpResponse.json(match);
  }),

  http.post(`${API}/agent/start`, () => {
    return HttpResponse.json({ task_id: "agent-1", status: "queued", result: null });
  }),

  http.post(`${API}/agent/resume/:threadId`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({
      task_id: "thread-1",
      status: "running",
      result: { action: body.action },
    });
  }),

  http.get(`${API}/config/preferences`, () => {
    return HttpResponse.json(makePreferences());
  }),

  http.put(`${API}/config/preferences`, () => {
    return HttpResponse.json(makePreferences());
  }),
];
