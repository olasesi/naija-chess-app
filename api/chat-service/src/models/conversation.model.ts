import mongoose, { Schema, Document } from "mongoose";

export interface IConversation extends Document {
  type: "direct" | "group";
  participants: {
    userId: string;
    joinedAt: Date;
    lastReadAt: Date;
  }[];
  name?: string;
  gameId?: string;
  lastMessage?: {
    content: string;
    senderId: string;
    sentAt: Date;
  };
  createdAt: Date;
  updatedAt: Date;
}

const conversationSchema = new Schema<IConversation>(
  {
    type: { type: String, enum: ["direct", "group"], required: true },
    participants: [
      {
        userId: { type: String, required: true },
        joinedAt: { type: Date, default: Date.now },
        lastReadAt: { type: Date, default: Date.now },
      },
    ],
    name: { type: String },
    gameId: { type: String },
    lastMessage: {
      content: { type: String },
      senderId: { type: String },
      sentAt: { type: Date },
    },
  },
  { timestamps: true }
);

conversationSchema.index({ "participants.userId": 1 });
conversationSchema.index({ gameId: 1 });
conversationSchema.index({ type: 1, "participants.userId": 1 });

export const Conversation = mongoose.model<IConversation>("Conversation", conversationSchema);
