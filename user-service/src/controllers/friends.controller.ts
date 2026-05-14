import { Request, Response } from "express";
import { FriendsService } from "../services/friends.service";
import { sendSuccess, sendError } from "../utils/response";

export const FriendsController = {
  async sendRequest(req: Request, res: Response): Promise<void> {
    try {
      const userId = req.user!.sub;
      const { friendId } = req.body;

      const friend = await FriendsService.sendRequest(userId, friendId);

      const messages: Record<string, string> = {
        CANNOT_FRIEND_SELF: "You cannot send a friend request to yourself",
        ALREADY_FRIENDS: "You are already friends with this user",
        REQUEST_ALREADY_EXISTS: "A friend request already exists",
        RELATIONSHIP_BLOCKED: "This relationship is blocked",
      };

      sendSuccess(res, { friend }, "Friend request sent", 201);
    } catch (err: any) {
      const messages: Record<string, string> = {
        CANNOT_FRIEND_SELF: "You cannot send a friend request to yourself",
        ALREADY_FRIENDS: "You are already friends with this user",
        REQUEST_ALREADY_EXISTS: "A friend request already exists",
        RELATIONSHIP_BLOCKED: "This relationship is blocked",
      };
      const status = err.message === "REQUEST_ALREADY_EXISTS" ? 409 : 400;
      sendError(res, messages[err.message] || "Failed to send friend request", status);
    }
  },

  async respondToRequest(req: Request, res: Response): Promise<void> {
    try {
      const userId = req.user!.sub;
      const { friendId } = req.params;
      const { action } = req.body;

      const friend = await FriendsService.respondToRequest(userId, friendId, action);

      const messages: Record<string, string> = {
        accept: "Friend request accepted",
        decline: "Friend request declined",
        block: "User blocked",
      };

      sendSuccess(res, { friend }, messages[action] || "Action completed");
    } catch (err: any) {
      const messages: Record<string, string> = {
        REQUEST_NOT_FOUND: "Friend request not found",
      };
      sendError(res, messages[err.message] || "Failed to respond to request", 404);
    }
  },

  async removeFriend(req: Request, res: Response): Promise<void> {
    try {
      const userId = req.user!.sub;
      const { friendId } = req.params;

      await FriendsService.removeFriend(userId, friendId);
      sendSuccess(res, null, "Friend removed");
    } catch (err: any) {
      sendError(res, err.message || "Failed to remove friend", 500);
    }
  },

  async getFriends(req: Request, res: Response): Promise<void> {
    try {
      const userId = req.user!.sub;
      const status = (req.query.status as "ACCEPTED" | "PENDING") || "ACCEPTED";

      const friends = await FriendsService.getFriends(userId, status);
      sendSuccess(res, { friends });
    } catch (err: any) {
      sendError(res, err.message || "Failed to get friends", 500);
    }
  },
};
