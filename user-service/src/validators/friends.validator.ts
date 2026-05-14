import { z } from "zod";

export const friendRequestSchema = z.object({
  friendId: z.string().uuid("Invalid user ID"),
});

export const friendActionSchema = z.object({
  action: z.enum(["accept", "decline", "block"]),
});
