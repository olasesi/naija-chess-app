# 🚀 Expo React Native Boilerplate

A production-ready Expo (Managed) boilerplate with Expo Router, strong typing, testing, monitoring, and a clean architecture.

---

## 📦 Stack

| Category         | Package                                    |
| ---------------- | ------------------------------------------ |
| **Framework**    | Expo ~52, React Native 0.76                |
| **Routing**      | Expo Router v4 (file-based)                |
| **Language**     | TypeScript (strict mode)                   |
| **Styling**      | NativeWind v4 (Tailwind for RN)            |
| **Animations**   | React Native Reanimated v3                 |
| **State**        | Zustand v5 + Immer                         |
| **Server State** | TanStack Query v5                          |
| **HTTP**         | Axios                                      |
| **Forms**        | React Hook Form + Zod                      |
| **Storage**      | MMKV (fast) + Expo SecureStore (sensitive) |
| **Monitoring**   | Sentry React Native                        |
| **Testing**      | Jest + Testing Library + MSW               |
| **Linting**      | ESLint + Prettier                          |
| **Git Hooks**    | Husky + lint-staged + commitlint           |

---

## 📁 Folder Structure

```
.
├── app/                    # Expo Router screens (file = route)
│   ├── _layout.tsx         # Root layout (providers, Sentry, fonts)
│   └── index.tsx           # Home screen
├── components/
│   ├── ui/                 # Reusable UI primitives (Button, Input, etc.)
│   └── layout/             # Layout components (Screen, Header, etc.)
├── hooks/                  # Custom React hooks
│   ├── useApi.ts           # Generic GET/mutate hooks
│   └── useValidatedForm.ts # RHF + Zod factory
├── stores/                 # Zustand stores
│   └── authStore.ts
├── lib/
│   ├── api/
│   │   ├── client.ts       # Axios instance with interceptors
│   │   └── queryClient.ts  # TanStack QueryClient config
│   └── utils/
│       └── storage.ts      # MMKV wrapper
├── constants/              # App-wide constants & query key factory
├── types/                  # Global TypeScript types
├── assets/fonts/           # Custom fonts
└── __tests__/
    ├── setup.ts            # Jest + MSW global setup
    ├── mocks/
    │   ├── handlers.ts     # MSW API route mocks
    │   └── server.ts
    ├── unit/               # Store, hook, util tests
    └── integration/        # Screen + flow tests
```

---

## 🛠 Getting Started

```bash
# 1. Clone & install
git clone <your-repo>
cd my-expo-app
npm install

# 2. Copy env file
cp .env.example .env
# Fill in your API URL and Sentry DSN

# 3. Start dev server
npx expo start
```

---

## 🧪 Testing

```bash
npm test              # Run all tests once
npm run test:watch    # Watch mode
npm run test:coverage # Coverage report (threshold: 70%)
```

Tests use **MSW** to intercept API calls — no real network requests in tests.

---

## 🔍 Linting & Formatting

```bash
npm run lint          # Check for lint errors
npm run lint:fix      # Auto-fix lint errors
npm run format        # Format all files with Prettier
npm run type-check    # TypeScript type checking
```

Pre-commit hooks (Husky) will run lint-staged automatically on `git commit`.

---

## 📊 Monitoring (Sentry)

Sentry is initialized in `app/_layout.tsx`. The root component is wrapped with `Sentry.wrap()` for automatic crash reporting.

Set your DSN in `.env`:

```
EXPO_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/yyy
```

**What's captured automatically:**

- JS crashes & unhandled promise rejections
- API errors (via Axios interceptor)
- Performance traces (`tracesSampleRate: 0.2` in prod)

---

## 📝 Commit Convention

Uses [Conventional Commits](https://conventionalcommits.org):

```
feat: add user profile screen
fix: resolve token refresh race condition
chore: update dependencies
test: add auth store unit tests
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `revert`, `ci`

---

## 🌿 Environment Variables

All client-side env vars must be prefixed with `EXPO_PUBLIC_`:

| Variable                 | Description           |
| ------------------------ | --------------------- |
| `EXPO_PUBLIC_API_URL`    | Base URL for your API |
| `EXPO_PUBLIC_SENTRY_DSN` | Sentry project DSN    |

---

## 🚢 Building for Production

```bash
# Install EAS CLI
npm install -g eas-cli

# Configure EAS (first time)
eas build:configure

# Build for iOS / Android
eas build --platform ios
eas build --platform android
```
