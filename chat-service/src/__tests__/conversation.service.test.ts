import { ConversationService } from "../services/conversation.service";

jest.mock("../models/conversation.model", () => ({
  Conversation: {
    findById: jest.fn(),
    findOne: jest.fn(),
    find: jest.fn(),
    create: jest.fn(),
    findByIdAndUpdate: jest.fn(),
    updateOne: jest.fn(),
  },
}));

jest.mock("../models/message.model", () => ({
  Message: {
    countDocuments: jest.fn(),
  },
}));

const { Conversation } = jest.requireMock("../models/conversation.model");
const { Message } = jest.requireMock("../models/message.model");

describe("ConversationService", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("create", () => {
    it("should create a direct conversation", async () => {
      Conversation.findOne.mockResolvedValue(null);
      Conversation.create.mockResolvedValue({
        _id: "conv-1",
        type: "direct",
        participants: [{ userId: "user-1" }, { userId: "user-2" }],
      });

      const result = await ConversationService.create({
        type: "direct",
        participants: [{ userId: "user-1" }, { userId: "user-2" }],
      });

      expect(Conversation.create).toHaveBeenCalled();
      expect(result._id).toBe("conv-1");
    });

    it("should return existing direct conversation", async () => {
      const existing = {
        _id: "existing-conv",
        type: "direct",
        participants: [{ userId: "user-1" }, { userId: "user-2" }],
      };
      Conversation.findOne.mockResolvedValue(existing);

      const result = await ConversationService.create({
        type: "direct",
        participants: [{ userId: "user-1" }, { userId: "user-2" }],
      });

      expect(Conversation.create).not.toHaveBeenCalled();
      expect(result._id).toBe("existing-conv");
    });
  });

  describe("getUserConversations", () => {
    it("should return sorted conversations", async () => {
      Conversation.find.mockReturnValue({
        sort: jest.fn().mockReturnValue({
          lean: jest.fn().mockResolvedValue([
            { _id: "conv-1", updatedAt: new Date("2024-02-01") },
            { _id: "conv-2", updatedAt: new Date("2024-01-01") },
          ]),
        }),
      });

      const result = await ConversationService.getUserConversations("user-1");

      expect(result).toHaveLength(2);
    });
  });

  describe("markAsRead", () => {
    it("should update lastReadAt", async () => {
      Conversation.updateOne.mockResolvedValue({ modifiedCount: 1 });

      await ConversationService.markAsRead("conv-1", "user-1");

      expect(Conversation.updateOne).toHaveBeenCalledWith(
        { _id: "conv-1", "participants.userId": "user-1" },
        expect.any(Object)
      );
    });
  });
});
