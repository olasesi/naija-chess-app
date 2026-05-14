import { Router } from "express";
import { FriendsController } from "../controllers/friends.controller";
import { authenticate } from "../middlewares/auth.middleware";
import { validate } from "../middlewares/validate";
import { friendRequestLimiter } from "../middlewares/rate-limit";
import {
  friendRequestSchema,
  friendActionSchema,
} from "../validators/friends.validator";

const router = Router();

router.get("/", authenticate, FriendsController.getFriends);
router.post(
  "/request",
  authenticate,
  friendRequestLimiter,
  validate(friendRequestSchema),
  FriendsController.sendRequest
);
router.patch(
  "/request/:friendId",
  authenticate,
  validate(friendActionSchema),
  FriendsController.respondToRequest
);
router.delete("/:friendId", authenticate, FriendsController.removeFriend);

export default router;
