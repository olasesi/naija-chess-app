import { Router } from "express";
import { z } from "zod";
import { ConversationController } from "../controllers/conversation.controller";
import { MessageController } from "../controllers/message.controller";
import { authenticate } from "../middlewares/auth.middleware";
import { validate } from "../middlewares/validate";

const router = Router();

const createConversationSchema = z.object({
  type: z.enum(["direct", "group"]),
  participants: z.array(z.union([z.string(), z.object({ userId: z.string() })])),
  name: z.string().optional(),
  gameId: z.string().optional(),
});

const sendMessageSchema = z.object({
  content: z.string().min(1).max(5000),
  type: z.enum(["text", "image"]).optional(),
});

const editMessageSchema = z.object({
  content: z.string().min(1).max(5000),
});

// Conversations
router.get("/conversations", authenticate, ConversationController.list);
router.post("/conversations", authenticate, validate(createConversationSchema), ConversationController.create);
router.get("/conversations/:conversationId", authenticate, ConversationController.getById);
router.post("/conversations/:conversationId/read", authenticate, ConversationController.markAsRead);

// Messages
router.get("/conversations/:conversationId/messages", authenticate, MessageController.list);
router.post("/conversations/:conversationId/messages", authenticate, validate(sendMessageSchema), MessageController.send);
router.put("/messages/:messageId", authenticate, validate(editMessageSchema), MessageController.edit);
router.delete("/messages/:messageId", authenticate, MessageController.delete);

export default router;
