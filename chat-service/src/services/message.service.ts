import { Message, IMessage } from "../models/message.model";
import { ConversationService } from "./conversation.service";

interface SendMessageInput {
  conversationId: string;
  senderId: string;
  type?: "text" | "system" | "image";
  content: string;
}

export const MessageService = {
  async send(input: SendMessageInput): Promise<IMessage> {
    const conversation = await ConversationService.findById(input.conversationId);
    if (!conversation) {
      throw new Error("CONVERSATION_NOT_FOUND");
    }

    const isParticipant = conversation.participants.some(
      (p) => p.userId === input.senderId
    );
    if (!isParticipant) {
      throw new Error("NOT_PARTICIPANT");
    }

    const message = await Message.create({
      conversationId: input.conversationId,
      senderId: input.senderId,
      type: input.type || "text",
      content: input.content,
    });

    await ConversationService.updateLastMessage(
      input.conversationId,
      input.content,
      input.senderId
    );

    return message;
  },

  async getMessages(
    conversationId: string,
    userId: string,
    limit = 50,
    before?: string
  ): Promise<{ messages: IMessage[]; hasMore: boolean }> {
    const conversation = await ConversationService.findById(conversationId);
    if (!conversation) throw new Error("CONVERSATION_NOT_FOUND");

    const isParticipant = conversation.participants.some(
      (p) => p.userId === userId
    );
    if (!isParticipant) throw new Error("NOT_PARTICIPANT");

    const query: any = {
      conversationId,
      deletedAt: null,
    };

    if (before) {
      query._id = { $lt: before };
    }

    const messages = await Message.find(query)
      .sort({ createdAt: -1 })
      .limit(limit + 1)
      .lean() as unknown as IMessage[];

    const hasMore = messages.length > limit;
    if (hasMore) messages.pop();

    return {
      messages: messages.reverse(),
      hasMore,
    };
  },

  async edit(messageId: string, userId: string, content: string): Promise<IMessage | null> {
    const message = await Message.findById(messageId);
    if (!message) throw new Error("MESSAGE_NOT_FOUND");
    if (message.senderId !== userId) throw new Error("NOT_AUTHOR");
    if (message.deletedAt) throw new Error("MESSAGE_DELETED");

    message.content = content;
    message.editedAt = new Date();
    await message.save();
    return message;
  },

  async softDelete(messageId: string, userId: string): Promise<void> {
    const message = await Message.findById(messageId);
    if (!message) throw new Error("MESSAGE_NOT_FOUND");
    if (message.senderId !== userId) throw new Error("NOT_AUTHOR");

    message.deletedAt = new Date();
    await message.save();
  },
};
