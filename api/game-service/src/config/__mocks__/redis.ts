export const redis = {
  get: jest.fn(async () => null),
  setex: jest.fn(async () => "OK"),
  set: jest.fn(async () => "OK"),
  del: jest.fn(async () => 1),
  getAsync: jest.fn(async () => null),
};

export const RedisKeys = {
  activeGame: (gameId: string) => `game:active:${gameId}`,
  userGame: (userId: string) => `game:user:${userId}`,
  clockTick: (gameId: string) => `game:clock:${gameId}`,
  matchmaking: (timeControl: string) => `mm:queue:${timeControl}`,
};