import { Router } from "express";
import profileRoutes from "./profile.routes";
import statsRoutes from "./stats.routes";
import friendsRoutes from "./friends.routes";
import preferencesRoutes from "./preferences.routes";

const router = Router();

router.use("/profiles", profileRoutes);
router.use("/stats", statsRoutes);
router.use("/friends", friendsRoutes);
router.use("/preferences", preferencesRoutes);

export default router;
