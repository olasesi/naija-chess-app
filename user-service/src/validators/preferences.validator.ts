import { z } from "zod";

export const updatePreferencesSchema = z.object({
  theme: z.enum(["dark", "light", "blue", "green"]).optional(),
  boardStyle: z.enum(["classic", "wood", "marble", "ice"]).optional(),
  pieceStyle: z.enum(["standard", "neo", "maestro", "alphazar"]).optional(),
  soundEnabled: z.boolean().optional(),
  showAnalysis: z.boolean().optional(),
  autoPromote: z.boolean().optional(),
});
