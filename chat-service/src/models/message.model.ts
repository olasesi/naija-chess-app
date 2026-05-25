import mongoose, { Schema, Document } from "mongoose";

export interface IMessage extends Document {
  conversationId: mongoose.Types.ObjectId;
  senderId: string;
  type: "text" | "system" | "image";
  content: string;
  editedAt?: Date;
  deletedAt?: Date;
  createdAt: Date;
}

const messageSchema = new Schema<IMessage>(
  {
    conversationId: {
      type: Schema.Types.ObjectId,
      ref: "Conversation",
      required: true,
      index: true,
    },
    senderId: { type: String, required: true },
    type: {
      type: String,
      enum: ["text", "system", "image"],
      default: "text",
    },
    content: { type: String, required: true },
    editedAt: { type: Date },
    deletedAt: { type: Date },
  },
  { timestamps: { createdAt: true, updatedAt: false } }
);

messageSchema.index({ conversationId: 1, createdAt: -1 });

export const Message = mongoose.model<IMessage>("Message", messageSchema);
