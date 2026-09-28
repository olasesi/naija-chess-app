module.exports = {
  testEnvironment: "node",
  roots: ["<rootDir>/src"],
  testMatch: ["**/__tests__/**/*.test.ts"],
  clearMocks: true,
  transform: {
    "^.+\\.ts$": ["ts-jest", {}],
  },
  moduleNameMapper: {
    "^[.][.]/config/env$": "<rootDir>/src/__tests__/__mocks__/env.ts",
    "^[.][.]/config/redis$": "<rootDir>/src/__tests__/__mocks__/redis.ts",
  },
};
