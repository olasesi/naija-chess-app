import { MessageService } from "../services/message.service";
import { ConversationService } from "../services/conversation.service";

// Mock the models
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
    create: jest.fn(),
    find: jest.fn(),
    findById: jest.fn(),
    countDocuments: jest.fn(),
  },
}));

const { Conversation } = jest.requireMock("../models/conversation.model");
const { Message } = jest.requireMock("../models/message.model");

describe("MessageService", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("send", () => {
    it("should send a message successfully", async () => {
      Conversation.findById.mockResolvedValue({
        _id: "conv-1",
        participants: [{ userId: "user-123" }],
      });
      Message.create.mockResolvedValue({
        _id: "msg-1",
        conversationId: "conv-1",
        senderId: "user-123",
        content: "Hello",
        createdAt: new Date(),
      });

      const result = await MessageService.send({
        conversationId: "conv-1",
        senderId: "user-123",
        content: "Hello",
      });

      expect(result.content).toBe("Hello");
      expect(Message.create).toHaveBeenCalledWith(
        expect.objectContaining({ content: "Hello" })
      );
    });

    it("should reject if conversation not found", async () => {
      Conversation.findById.mockResolvedValue(null);

      await expect(
        MessageService.send({
          conversationId: "conv-1",
          senderId: "user-123",
          content: "Hello",
        })
      ).rejects.toThrow("CONVERSATION_NOT_FOUND");
    });

    it("should reject if user is not a participant", async () => {
      Conversation.findById.mockResolvedValue({
        _id: "conv-1",
        participants: [{ userId: "other-user" }],
      });

      await expect(
        MessageService.send({
          conversationId: "conv-1",
          senderId: "user-123",
          content: "Hello",
        })
      ).rejects.toThrow("NOT_PARTICIPANT");
    });
  });

  describe("getMessages", () => {
    it("should return paginated messages", async () => {
      Conversation.findById.mockResolvedValue({
        _id: "conv-1",
        participants: [{ userId: "user-123" }],
      });
      Message.find.mockReturnValue({
        sort: jest.fn().mockReturnValue({
          limit: jest.fn().mockReturnValue({
            lean: jest.fn().mockResolvedValue([
              { _id: "1", content: "Hi", createdAt: new Date("2024-01-01") },
            ]),
          }),
        }),
      });

      const result = await MessageService.getMessages("conv-1", "user-123", 50);

      expect(result.messages).toHaveLength(1);
      expect(result.hasMore).toBe(false);
    });
  });

  describe("edit", () => {
    it("should edit own message", async () => {
      const saveMock = jest.fn();
      Message.findById.mockResolvedValue({
        _id: "msg-1",
        senderId: "user-123",
        content: "Old",
        deletedAt: null,
        save: saveMock,
      });

      await MessageService.edit("msg-1", "user-123", "Updated");

      expect(saveMock).toHaveBeenCalled();
    });

    it("should reject editing deleted message", async () => {
      Message.findById.mockResolvedValue({
        _id: "msg-1",
        senderId: "user-123",
        deletedAt: new Date(),
      });

      await expect(
        MessageService.edit("msg-1", "user-123", "Updated")
      ).rejects.toThrow("MESSAGE_DELETED");
    });
  });

  describe("softDelete", () => {
    it("should soft delete own message", async () => {
      const saveMock = jest.fn();
      Message.findById.mockResolvedValue({
        _id: "msg-1",
        senderId: "user-123",
        save: saveMock,
      });

      await MessageService.softDelete("msg-1", "user-123");

      expect(saveMock).toHaveBeenCalled();
    });
  });
});
