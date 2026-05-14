import { z } from "zod";

export const updateProfileSchema = z.object({
  displayName: z
    .string()
    .min(2, "Display name must be at least 2 characters")
    .max(30, "Display name must be at most 30 characters")
    .optional(),
  bio: z
    .string()
    .max(500, "Bio must be at most 500 characters")
    .optional(),
  country: z
    .string()
    .length(2, "Country must be a 2-letter ISO code")
    .optional(),
  title: z
    .string()
    .max(10)
    .optional(),
});
