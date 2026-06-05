import { Request, Response } from "express";
import { MessageService } from "../services/message.service";
import { sendSuccess, sendError } from "../utils/response";

export const MessageController = {
  async list(req: Request, res: Response): Promise<void> {
    try {
      const limit = parseInt(req.query.limit as string) || 50;
      const before = req.query.before as string | undefined;

      const result = await MessageService.getMessages(
        req.params.conversationId,
        req.user!.sub,
        limit,
        before
      );
      sendSuccess(res, result);
    } catch (err: any) {
      const status =
        err.message === "CONVERSATION_NOT_FOUND"
          ? 404
          : err.message === "NOT_PARTICIPANT"
          ? 403
          : 500;
      sendError(res, err.message || "Failed to get messages", status);
    }
  },

  async send(req: Request, res: Response): Promise<void> {
    try {
      const message = await MessageService.send({
        conversationId: req.params.conversationId,
        senderId: req.user!.sub,
        content: req.body.content,
        type: req.body.type,
      });
      sendSuccess(res, { message }, "Message sent", 201);
    } catch (err: any) {
      const status =
        err.message === "CONVERSATION_NOT_FOUND"
          ? 404
          : err.message === "NOT_PARTICIPANT"
          ? 403
          : 500;
      sendError(res, err.message || "Failed to send message", status);
    }
  },

  async edit(req: Request, res: Response): Promise<void> {
    try {
      const message = await MessageService.edit(
        req.params.messageId,
        req.user!.sub,
        req.body.content
      );
      sendSuccess(res, { message }, "Message edited");
    } catch (err: any) {
      const status =
        err.message === "MESSAGE_NOT_FOUND"
          ? 404
          : err.message === "NOT_AUTHOR"
          ? 403
          : err.message === "MESSAGE_DELETED"
          ? 400
          : 500;
      sendError(res, err.message || "Failed to edit message", status);
    }
  },

  async delete(req: Request, res: Response): Promise<void> {
    try {
      await MessageService.softDelete(req.params.messageId, req.user!.sub);
      sendSuccess(res, null, "Message deleted");
    } catch (err: any) {
      const status =
        err.message === "MESSAGE_NOT_FOUND"
          ? 404
          : err.message === "NOT_AUTHOR"
          ? 403
          : 500;
      sendError(res, err.message || "Failed to delete message", status);
    }
  },
};
