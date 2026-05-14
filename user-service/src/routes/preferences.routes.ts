import { Router } from "express";
import { PreferencesController } from "../controllers/preferences.controller";
import { authenticate } from "../middlewares/auth.middleware";
import { validate } from "../middlewares/validate";
import { updatePreferencesSchema } from "../validators/preferences.validator";

const router = Router();

router.get("/", authenticate, PreferencesController.getPreferences);
router.patch(
  "/",
  authenticate,
  validate(updatePreferencesSchema),
  PreferencesController.updatePreferences
);

export default router;
