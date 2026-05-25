import { Conversation, IConversation } from "../models/conversation.model";
import { Message } from "../models/message.model";
import { redis, RedisKeys } from "../config/redis";

interface ParticipantInput {
  userId: string;
  joinedAt?: Date;
}

interface CreateConversationInput {
  type: "direct" | "group";
  participants: ParticipantInput[];
  name?: string;
  gameId?: string;
}

export const ConversationService = {
  async create(input: CreateConversationInput): Promise<IConversation> {
    if (input.type === "direct") {
      const existing = await Conversation.findOne({
        type: "direct",
        "participants.userId": { $all: input.participants.map((p) => p.userId) },
      });
      if (existing) return existing;
    }

    const conversation = await Conversation.create({
      type: input.type,
      participants: input.participants,
      name: input.name,
      gameId: input.gameId,
    });

    return conversation;
  },

  async findById(conversationId: string): Promise<IConversation | null> {
    return Conversation.findById(conversationId);
  },

  async getUserConversations(userId: string): Promise<IConversation[]> {
    return Conversation.find({ "participants.userId": userId })
      .sort({ updatedAt: -1 })
      .lean() as unknown as Promise<IConversation[]>;
  },

  async getByGameId(gameId: string): Promise<IConversation | null> {
    return Conversation.findOne({ gameId });
  },

  async addParticipant(conversationId: string, userId: string): Promise<IConversation | null> {
    return Conversation.findByIdAndUpdate(
      conversationId,
      { $push: { participants: { userId, joinedAt: new Date(), lastReadAt: new Date() } } },
      { new: true }
    );
  },

  async markAsRead(conversationId: string, userId: string): Promise<void> {
    await Conversation.updateOne(
      { _id: conversationId, "participants.userId": userId },
      { $set: { "participants.$.lastReadAt": new Date() } }
    );
  },

  async updateLastMessage(
    conversationId: string,
    content: string,
    senderId: string
  ): Promise<void> {
    await Conversation.findByIdAndUpdate(conversationId, {
      lastMessage: { content, senderId, sentAt: new Date() },
      updatedAt: new Date(),
    });
  },

  async getUnreadCount(userId: string): Promise<number> {
    const conversations = await Conversation.find({ "participants.userId": userId }).lean();
    let unread = 0;

    for (const conv of conversations) {
      const participant = conv.participants.find((p) => p.userId === userId);
      if (!participant) continue;

      const count = await Message.countDocuments({
        conversationId: conv._id,
        senderId: { $ne: userId },
        createdAt: { $gt: participant.lastReadAt },
        deletedAt: null,
      });
      unread += count;
    }

    return unread;
  },
};
