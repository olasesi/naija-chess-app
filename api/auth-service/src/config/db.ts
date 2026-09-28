import { PrismaClient } from "@prisma/client";
import { env } from "./env";

declare global {
  var __prisma: PrismaClient | undefined;
}

// Prevent multiple instances in development (hot reload)
export const prisma =
  global.__prisma ||
  new PrismaClient({
    log:
      env.NODE_ENV === "development" ? ["query", "error", "warn"] : ["error"],
  });

if (env.NODE_ENV !== "production") {
  global.__prisma = prisma;
}

export async function connectDB(): Promise<void> {
  try {
    await prisma.$connect();
    console.log("✅ MySQL connected via Prisma");
  } catch (error) {
    console.error("❌ MySQL connection failed:", error);
    process.exit(1);
  }
}

export async function disconnectDB(): Promise<void> {
  await prisma.$disconnect();
}
