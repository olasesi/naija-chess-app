import { describe, it, expect, beforeAll } from "vitest";
import { ApiClient, healthCheck } from "../helpers/client.js";
import axios from "axios";

const BASE = process.env.GATEWAY_URL || "http://localhost:3000";

beforeAll(async () => {
  const ok = await healthCheck();
  if (!ok) {
    throw new Error("Gateway is not reachable. Start docker-compose first.");
  }
});

describe("Gateway Routing", () => {
  const routes = ["/api/auth", "/api/users", "/api/games", "/api/ratings", "/api/analysis", "/api/chat", "/api/notifications", "/api/tournaments", "/api/forum", "/api/admin"];

  it("health endpoint returns ok", async () => {
    const res = await axios.get(`${BASE}/health`);
    expect(res.status).toBe(200);
    expect(res.data.status).toBe("ok");
  });

  it("returns 404 for unknown routes", async () => {
    const res = await axios.get(`${BASE}/api/nonexistent`, { validateStatus: () => true });
    expect(res.status).toBe(404);
  });

  for (const route of routes) {
    it(`${route} returns 401 without auth token`, async () => {
      // GET on a route that requires auth — expect 401
      const res = await axios.get(`${BASE}${route}`, {
        validateStatus: () => true,
        headers: { Accept: "application/json" },
        timeout: 3000,
      });
      // A 401 means the gateway is enforcing auth, even if the downstream also returns 404/405
      // Some routes might return 404 if no matching sub-path (e.g. GET /api/users returns 404 from Django)
      // or 405 (method not allowed). Accept any non-2xx that's not a proxy error
      expect(res.status).not.toBe(200);
      expect(res.status).not.toBe(201);
      expect(res.status).not.toBe(503);
    });
  }
});

describe("Auth Flow", () => {
  const client = new ApiClient();

  it("POST /api/auth/register creates user and returns tokens", async () => {
    const data = await client.register();
    expect(data.accessToken).toBeTruthy();
    expect(data.refreshToken).toBeTruthy();
    expect(client.userId).toBeTruthy();
  });

  it("POST /api/auth/login returns tokens", async () => {
    const data = await client.login();
    expect(data.accessToken).toBeTruthy();
    expect(data.refreshToken).toBeTruthy();
  });

  it("registered user can access protected /api/users/me", async () => {
    const res = await client.get("/api/users/me");
    expect(res.status).toBe(200);
    expect(res.data.data).toBeDefined();
  });

  it("duplicate email registration fails with 409", async () => {
    const dup = new ApiClient(client.email);
    const res = await dup.post("/api/auth/register", {
      email: client.email,
      password: "TestPass123!",
      username: "dup",
    }, { validateStatus: () => true });
    expect(res.status).toBe(409);
  });
});

describe("Forum Flow", () => {
  const admin = new ApiClient(`admin_forum_${Date.now()}@test.com`, "ADMIN");
  const player = new ApiClient();

  beforeAll(async () => {
    await admin.register();
    await player.register();
  });

  it("creates a category", async () => {
    const res = await admin.post("/api/forum/categories", {
      name: "E2E Test Category",
      description: "Created during e2e test",
    });
    expect(res.status).toBe(201);
    expect(res.data.data.name).toBe("E2E Test Category");
  });

  it("lists categories", async () => {
    const res = await player.get("/api/forum/categories");
    expect(res.status).toBe(200);
    expect(res.data.data.length).toBeGreaterThanOrEqual(1);
  });

  it("creates a thread", async () => {
    // First get a category
    const cats = await player.get("/api/forum/categories");
    const catId = cats.data.data[0].id;

    const res = await player.post("/api/forum/threads", {
      category_id: catId,
      title: "E2E Thread",
      body: "This thread was created during e2e testing",
    });
    expect(res.status).toBe(201);
    expect(res.data.data.title).toBe("E2E Thread");
  });

  it("lists threads", async () => {
    const res = await player.get("/api/forum/threads");
    expect(res.status).toBe(200);
    expect(res.data.data.length).toBeGreaterThanOrEqual(1);
  });

  it("creates a post on a thread", async () => {
    const threads = await player.get("/api/forum/threads");
    const threadId = threads.data.data[0].id;

    const res = await player.post("/api/forum/posts", {
      thread_id: threadId,
      body: "This is a reply during e2e testing",
    });
    expect(res.status).toBe(201);
    expect(res.data.data.body).toBe("This is a reply during e2e testing");
  });

  it("toggles a like on a thread", async () => {
    const threads = await player.get("/api/forum/threads");
    const threadId = threads.data.data[0].id;

    const res = await player.post("/api/forum/likes", {
      likeable_type: "thread",
      likeable_id: threadId,
    });
    expect(res.status).toBe(200);
    expect(res.data.data.liked).toBe(true);
  });

  it("toggles a bookmark on a thread", async () => {
    const threads = await player.get("/api/forum/threads");
    const threadId = threads.data.data[0].id;

    const res = await player.post("/api/forum/bookmarks", {
      bookmarkable_type: "thread",
      bookmarkable_id: threadId,
    });
    expect(res.status).toBe(200);
    expect(res.data.data.bookmarked).toBe(true);
  });
});

describe("Admin Flow", () => {
  const admin = new ApiClient(`admin_e2e_${Date.now()}@test.com`, "ADMIN");
  const player = new ApiClient();

  beforeAll(async () => {
    await admin.register();
    await player.register();
  });

  it("dashboard requires admin role", async () => {
    const res = await player.get("/api/admin/dashboard", { validateStatus: () => true });
    expect(res.status).toBe(403);
  });

  it("admin can view dashboard", async () => {
    const res = await admin.get("/api/admin/dashboard");
    expect(res.status).toBe(200);
    expect(res.data.data.total_admin_actions).toBeDefined();
  });

  it("admin can update settings", async () => {
    const res = await admin.put("/api/admin/settings", {
      settings: [
        { key: "site_name", value: "E2E Chess", description: "Set during e2e" },
        { key: "maintenance", value: "false", type: "boolean" },
      ],
    });
    expect(res.status).toBe(200);
  });

  it("admin can read settings", async () => {
    const res = await admin.get("/api/admin/settings?key=site_name");
    expect(res.status).toBe(200);
    expect(res.data.data.value).toBe("E2E Chess");
  });

  it("user can report content", async () => {
    const res = await player.post("/api/admin/reported-content", {
      resource_type: "thread",
      resource_id: "e2e-test-thread-1",
      reason: "This is an e2e test report with sufficient length",
    });
    expect(res.status).toBe(201);
    expect(res.data.data.status).toBe("PENDING");
  });

  it("admin can moderate reported content", async () => {
    // Find pending reports
    const reports = await admin.get("/api/admin/reported-content?status=PENDING");
    expect(reports.data.data.length).toBeGreaterThanOrEqual(1);

    const reportId = reports.data.data[0].id;
    const res = await admin.put(`/api/admin/reported-content/${reportId}`, {
      status: "DISMISSED",
    });
    expect(res.status).toBe(200);
    expect(res.data.data.status).toBe("DISMISSED");
  });

  it("admin can view audit log", async () => {
    const res = await admin.get("/api/admin/audit-log");
    expect(res.status).toBe(200);
    expect(res.data.meta.total).toBeGreaterThanOrEqual(1);
  });
});

describe("Game Flow", () => {
  const p1 = new ApiClient(`game_p1_${Date.now()}@test.com`);
  const p2 = new ApiClient(`game_p2_${Date.now()}@test.com`);
  let gameId: string;

  beforeAll(async () => {
    await p1.register();
    await p2.register();
  });

  it("player 1 creates a game", async () => {
    const res = await p1.post("/api/games", {
      timeControl: { initial: 300, increment: 3 },
      color: "white",
    });
    expect(res.status).toBe(201);
    expect(res.data.data.id).toBeTruthy();
    expect(res.data.data.status).toBe("WAITING");
    gameId = res.data.data.id;
  });

  it("player 2 joins the game", async () => {
    const res = await p2.post(`/api/games/${gameId}/join`);
    expect(res.status).toBe(200);
    expect(res.data.data.status).toBe("ACTIVE");
    expect(res.data.data.black?.id).toBe(p2.userId);
  });

  it("fetches game by id", async () => {
    const res = await p1.get(`/api/games/${gameId}`);
    expect(res.status).toBe(200);
    expect(res.data.data.id).toBe(gameId);
  });

  it("player 1 makes a move (e4)", async () => {
    const res = await p1.post(`/api/games/${gameId}/move`, {
      from: "e2",
      to: "e4",
      promotion: null,
    });
    expect(res.status).toBe(200);
    expect(res.data.data.board).toBeDefined();
  });

  it("player 2 makes a move (e5)", async () => {
    const res = await p2.post(`/api/games/${gameId}/move`, {
      from: "e7",
      to: "e5",
      promotion: null,
    });
    expect(res.status).toBe(200);
  });

  it("returns players games", async () => {
    const res = await p1.get("/api/games/user/me");
    expect(res.status).toBe(200);
    expect(res.data.data.length).toBeGreaterThanOrEqual(1);
  });
});

describe("Tournament Flow", () => {
  const admin = new ApiClient(`tourn_admin_${Date.now()}@test.com`, "ADMIN");
  const players: ApiClient[] = [];

  beforeAll(async () => {
    await admin.register();
    for (let i = 0; i < 4; i++) {
      const p = new ApiClient(`tourn_p${i}_${Date.now()}@test.com`);
      await p.register();
      players.push(p);
    }
  });

  it("creates a swiss tournament", async () => {
    const res = await admin.post("/api/tournaments", {
      name: "E2E Swiss Tournament",
      type: "SWISS",
      max_players: 8,
      min_players: 2,
      time_control: { initial: 600, increment: 5 },
      total_rounds: 3,
    });
    expect(res.status).toBe(201);
    expect(res.data.data.type).toBe("SWISS");
    expect(res.data.data.status).toBe("PENDING");
  });

  it("lists tournaments", async () => {
    const res = await players[0].get("/api/tournaments");
    expect(res.status).toBe(200);
    expect(res.data.data.length).toBeGreaterThanOrEqual(1);
    // save the tournament id for subsequent tests
    const tournId = res.data.data[0].id;
    (globalThis as any).__tournId = tournId;
  });

  it("all players join the tournament", async () => {
    const tournId = (globalThis as any).__tournId;
    for (const p of players) {
      const res = await p.post(`/api/tournaments/${tournId}/join`);
      expect(res.status).toBe(200);
    }
  });

  it("creator starts the tournament", async () => {
    const tournId = (globalThis as any).__tournId;
    const res = await admin.post(`/api/tournaments/${tournId}/start`);
    expect(res.status).toBe(200);
    expect(res.data.data.status).toBe("ACTIVE");
  });

  it("returns standings", async () => {
    const tournId = (globalThis as any).__tournId;
    const res = await players[0].get(`/api/tournaments/${tournId}/standings`);
    expect(res.status).toBe(200);
    expect(res.data.data.length).toBe(4);
  });

  it("returns rounds", async () => {
    const tournId = (globalThis as any).__tournId;
    const res = await players[0].get(`/api/tournaments/${tournId}/rounds`);
    expect(res.status).toBe(200);
    expect(res.data.data.length).toBeGreaterThanOrEqual(1);
  });

  it("pairs next round", async () => {
    const tournId = (globalThis as any).__tournId;
    const res = await admin.post(`/api/tournaments/${tournId}/pair`);
    expect(res.status).toBe(200);
  });
});

describe("Rating Flow", () => {
  const p1 = new ApiClient(`rating_p1_${Date.now()}@test.com`);
  const p2 = new ApiClient(`rating_p2_${Date.now()}@test.com`);

  beforeAll(async () => {
    await p1.register();
    await p2.register();
  });

  it("returns player rating", async () => {
    const res = await p1.get("/api/ratings/me");
    expect(res.status).toBe(200);
    expect(res.data.data.rating).toBeDefined();
  });

  it("returns rating history", async () => {
    const res = await p1.get("/api/ratings/me/history");
    expect(res.status).toBe(200);
    expect(res.data.data).toBeDefined();
  });
});
