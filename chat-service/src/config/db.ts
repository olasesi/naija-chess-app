import mongoose from "mongoose";
import { env } from "./env";

export async function connectDB(): Promise<void> {
  try {
    await mongoose.connect(env.MONGODB_URI);
    console.log("MongoDB connected [chat-service]");
  } catch (error) {
    console.error("MongoDB connection failed [chat-service]:", error);
    process.exit(1);
  }
}

export async function disconnectDB(): Promise<void> {
  await mongoose.disconnect();
}
