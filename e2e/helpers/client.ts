import axios, { AxiosInstance, AxiosRequestConfig } from "axios";

const BASE_URL = process.env.GATEWAY_URL || "http://localhost:3000";

export class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  public userId: string | null = null;
  public email: string;
  public role: string;

  constructor(email?: string, role: string = "PLAYER") {
    this.email = email || `e2e_${Date.now()}_${Math.random().toString(36).slice(2, 6)}@test.com`;
    this.role = role;

    this.client = axios.create({
      baseURL: BASE_URL,
      timeout: 10000,
      headers: { "Content-Type": "application/json" },
    });
  }

  setTokens(access: string, refresh?: string) {
    this.accessToken = access;
    if (refresh) this.refreshToken = refresh;
  }

  private getHeaders(extra: Record<string, string> = {}): Record<string, string> {
    const headers: Record<string, string> = { ...extra };
    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }
    return headers;
  }

  async register(password = "TestPass123!"): Promise<{ accessToken: string; refreshToken: string; userId: string }> {
    const res = await this.client.post("/api/auth/register", {
      email: this.email,
      password,
      username: this.email.split("@")[0],
    });
    if (res.data?.data?.accessToken) {
      this.accessToken = res.data.data.accessToken;
      this.refreshToken = res.data.data.refreshToken;
      this.userId = res.data.data.user?.id || res.data.data.userId;
    }
    return res.data.data;
  }

  async login(password = "TestPass123!"): Promise<{ accessToken: string; refreshToken: string }> {
    const res = await this.client.post("/api/auth/login", {
      email: this.email,
      password,
    });
    if (res.data?.data?.accessToken) {
      this.accessToken = res.data.data.accessToken;
      this.refreshToken = res.data.data.refreshToken;
    }
    return res.data.data;
  }

  async get(url: string, config?: AxiosRequestConfig) {
    return this.client.get(url, { ...config, headers: this.getHeaders(config?.headers as Record<string, string>) });
  }

  async post(url: string, data?: any, config?: AxiosRequestConfig) {
    return this.client.post(url, data, { ...config, headers: this.getHeaders(config?.headers as Record<string, string>) });
  }

  async put(url: string, data?: any, config?: AxiosRequestConfig) {
    return this.client.put(url, data, { ...config, headers: this.getHeaders(config?.headers as Record<string, string>) });
  }

  async delete(url: string, config?: AxiosRequestConfig) {
    return this.client.delete(url, { ...config, headers: this.getHeaders(config?.headers as Record<string, string>) });
  }
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await axios.get(`${BASE_URL}/health`, { timeout: 5000 });
    return res.status === 200;
  } catch {
    return false;
  }
}
