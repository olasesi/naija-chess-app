import { Router } from "express";
import { ProfileController } from "../controllers/profile.controller";
import { authenticate } from "../middlewares/auth.middleware";
import { validate } from "../middlewares/validate";
import { upload, handleUploadError } from "../middlewares/upload";
import { updateProfileSchema } from "../validators/profile.validator";

const router = Router();

router.get("/me", authenticate, ProfileController.getProfile);
router.get("/search", authenticate, ProfileController.searchProfiles);
router.get("/:userId", authenticate, ProfileController.getProfile);
router.patch(
  "/me",
  authenticate,
  validate(updateProfileSchema),
  ProfileController.updateProfile
);
router.post(
  "/me/avatar",
  authenticate,
  upload.single("avatar"),
  handleUploadError,
  ProfileController.uploadAvatar
);

export default router;
