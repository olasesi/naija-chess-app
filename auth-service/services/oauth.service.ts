import { OAuth2Client } from "google-auth-library";
import { env } from "../config/env";

const client = new OAuth2Client(env.GOOGLE_CLIENT_ID);

export interface GoogleUserInfo {
  googleId: string;
  email: string;
  name: string;
  avatar?: string;
  isVerified: boolean;
}

export const OAuthService = {
  // Verify the ID token sent from the frontend after Google Sign-In
  async verifyGoogleToken(idToken: string): Promise<GoogleUserInfo> {
    const ticket = await client.verifyIdToken({
      idToken,
      audience: env.GOOGLE_CLIENT_ID,
    });

    const payload = ticket.getPayload();

    if (!payload || !payload.email) {
      throw new Error("Invalid Google token");
    }

    return {
      googleId: payload.sub,
      email: payload.email,
      name: payload.name || payload.email.split("@")[0],
      avatar: payload.picture,
      isVerified: payload.email_verified ?? false,
    };
  },
};
