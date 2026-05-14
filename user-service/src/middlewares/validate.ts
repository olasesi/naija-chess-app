import { Request, Response, NextFunction } from "express";
import { z, ZodSchema } from "zod";
import { sendError } from "../utils/response";

export const validate =
  (schema: ZodSchema) =>
  (req: Request, res: Response, next: NextFunction): void => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      sendError(
        res,
        "Validation failed",
        422,
        result.error.flatten().fieldErrors
      );
      return;
    }
    req.body = result.data;
    next();
  };
