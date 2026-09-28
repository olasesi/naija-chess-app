export const redis = {
  setex: jest.fn().mockResolvedValue("OK"),
  set: jest.fn().mockResolvedValue("OK"),
  get: jest.fn().mockResolvedValue(null),
  del: jest.fn().mockResolvedValue(1),
  sadd: jest.fn().mockResolvedValue(1),
  srem: jest.fn().mockResolvedValue(1),
  smembers: jest.fn().mockResolvedValue([]),
  status: "ready",
  disconnect: jest.fn(),
};

export const RedisKeys = {
  userOnline: (u: string) => `chat:online:${u}`,
  typing: (c: string) => `chat:typing:${c}`,
  conversation: (c: string) => `chat:conv:${c}`,
};
