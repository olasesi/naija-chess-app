import { Server } from "socket.io";
import { AuthenticatedSocket } from "./auth.socket";
import { MessageService } from "../services/message.service";
import { ConversationService } from "../services/conversation.service";
import { redis, RedisKeys } from "../config/redis";
import { logger } from "../utils/logger";

export function registerChatHandlers(io: Server, socket: AuthenticatedSocket): void {
  const userId = socket.userId!;

  // Join all user's conversation rooms on connect
  socket.on("chat:join", async (conversationId: string) => {
    try {
      const conv = await ConversationService.findById(conversationId);
      if (!conv) {
        socket.emit("chat:error", { message: "Conversation not found" });
        return;
      }
      const isParticipant = conv.participants.some((p) => p.userId === userId);
      if (!isParticipant) {
        socket.emit("chat:error", { message: "Not a participant" });
        return;
      }
      socket.join(`chat:${conversationId}`);
    } catch (err) {
      logger.error("chat:join error", err);
    }
  });

  socket.on("chat:leave", (conversationId: string) => {
    socket.leave(`chat:${conversationId}`);
  });

  // Send a message
  socket.on("chat:send", async (data: { conversationId: string; content: string; type?: string }) => {
    try {
      const message = await MessageService.send({
        conversationId: data.conversationId,
        senderId: userId,
        content: data.content,
        type: data.type as any,
      });

      io.to(`chat:${data.conversationId}`).emit("chat:message", {
        conversationId: data.conversationId,
        message,
      });
    } catch (err: any) {
      socket.emit("chat:error", { message: err.message || "Failed to send" });
    }
  });

  // Typing indicator (throttled via Redis)
  socket.on("chat:typing", async (data: { conversationId: string; isTyping: boolean }) => {
    const typingKey = RedisKeys.typing(data.conversationId);
    const ttl = 3; // seconds

    if (data.isTyping) {
      await redis.setex(`${typingKey}:${userId}`, ttl, "1");
    } else {
      await redis.del(`${typingKey}:${userId}`);
    }

    socket.to(`chat:${data.conversationId}`).emit("chat:typing", {
      conversationId: data.conversationId,
      userId,
      isTyping: data.isTyping,
    });
  });

  // Mark conversation as read
  socket.on("chat:read", async (conversationId: string) => {
    try {
      await ConversationService.markAsRead(conversationId, userId);
      io.to(`chat:${conversationId}`).emit("chat:read", {
        conversationId,
        userId,
        readAt: new Date(),
      });
    } catch (err) {
      logger.error("chat:read error", err);
    }
  });

  // Track online status
  const onlineKey = RedisKeys.userOnline(userId);
  redis.sadd("chat:online:users", userId);
  redis.setex(onlineKey, 30, "1");

  // Periodic heartbeat to keep online status fresh
  const heartbeat = setInterval(async () => {
    try {
      await redis.setex(onlineKey, 30, "1");
    } catch {
      clearInterval(heartbeat);
    }
  }, 15000);

  socket.on("disconnect", async () => {
    clearInterval(heartbeat);
    await redis.srem("chat:online:users", userId);
    await redis.del(onlineKey);
    logger.info(`Chat socket disconnected: ${userId}`);
  });
}
