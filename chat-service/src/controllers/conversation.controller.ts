import { Request, Response } from "express";
import { ConversationService } from "../services/conversation.service";
import { sendSuccess, sendError } from "../utils/response";

export const ConversationController = {
  async create(req: Request, res: Response): Promise<void> {
    try {
      const { type, participants, name, gameId } = req.body;

      const allParticipants = [
        { userId: req.user!.sub },
        ...(participants || []).map((p: any) =>
          typeof p === "string" ? { userId: p } : p
        ),
      ];

      const conversation = await ConversationService.create({
        type,
        participants: allParticipants,
        name,
        gameId,
      });
      sendSuccess(res, { conversation }, "Conversation created", 201);
    } catch (err: any) {
      sendError(res, err.message || "Failed to create conversation", 500);
    }
  },

  async list(req: Request, res: Response): Promise<void> {
    try {
      const conversations = await ConversationService.getUserConversations(
        req.user!.sub
      );

      const convsWithUnread = await Promise.all(
        conversations.map(async (conv) => {
          const participant = conv.participants.find(
            (p: any) => p.userId === req.user!.sub
          );
          return { ...conv, unreadCount: 0 };
        })
      );

      sendSuccess(res, { conversations: convsWithUnread });
    } catch (err: any) {
      sendError(res, err.message || "Failed to list conversations", 500);
    }
  },

  async getById(req: Request, res: Response): Promise<void> {
    try {
      const conversation = await ConversationService.findById(
        req.params.conversationId
      );
      if (!conversation) {
        sendError(res, "Conversation not found", 404);
        return;
      }
      sendSuccess(res, { conversation });
    } catch (err: any) {
      sendError(res, err.message || "Failed to get conversation", 500);
    }
  },

  async markAsRead(req: Request, res: Response): Promise<void> {
    try {
      await ConversationService.markAsRead(
        req.params.conversationId,
        req.user!.sub
      );
      sendSuccess(res, null, "Marked as read");
    } catch (err: any) {
      sendError(res, err.message || "Failed to mark as read", 500);
    }
  },
};
