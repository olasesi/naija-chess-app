# E2E Integration Tests

Cross-service integration tests for the chess platform.

## Prerequisites

- Node.js 18+
- Docker + Docker Compose
- All services running:

```bash
docker compose up -d
```

## Install

```bash
cd e2e
npm install
```

## Run

```bash
# Full test suite (requires docker-compose services running)
npm test

# Watch mode for development
npm run test:watch
```

## Test Coverage

| Test | What it validates |
|------|-------------------|
| **Gateway Routing** | Health check, 404 on unknown routes, 401 on protected routes, all 10 service routes reachable |
| **Auth Flow** | Register, login, duplicate email rejection, protected endpoint access |
| **Forum Flow** | Category CRUD, thread CRUD, posts, likes, bookmarks — full read/write cycle |
| **Admin Flow** | Role enforcement (403 for non-admin), dashboard stats, settings CRUD, content reporting + moderation, audit log |
| **Game Flow** | Create game (WAITING), join (ACTIVE), make moves for both players, list player's games |
| **Tournament Flow** | Create Swiss tournament, list, all 4 players join, start (ACTIVE), standings, rounds, pair next round |
| **Rating Flow** | Get player rating, get rating history |

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `GATEWAY_URL` | `http://localhost:3000` | Base URL of the API Gateway |
