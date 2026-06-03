import axios, { AxiosInstance } from "axios";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "");

const http: AxiosInstance = axios.create({
  baseURL: apiBaseUrl ? `${apiBaseUrl}/api/v1` : "/api/v1",
  timeout: 300_000,
});

http.interceptors.request.use(cfg => {
  const token = localStorage.getItem("cl_token");
  if (token && cfg.headers) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
}, err => Promise.reject(err));

http.interceptors.response.use(
  r => r,
  err => {
    // Only redirect on 401 if not already on login page
    if (err.response?.status === 401 && !window.location.pathname.includes("/login")) {
      localStorage.removeItem("cl_token");
      localStorage.removeItem("cl_user");
      // Use setTimeout to avoid race conditions with redirect
      setTimeout(() => {
        window.location.href = "/login";
      }, 0);
    }
    return Promise.reject(err);
  }
);

const extractError = (err: unknown): string => {
  if (axios.isAxiosError(err)) {
    return err.response?.data?.detail || err.response?.data?.message || err.message || "Network error";
  }
  if (err instanceof Error) {
    return err.message;
  }
  return String(err || "Unknown error");
};

// ─── Auth ────────────────────────────────────────────────────────────────────
export const authApi = {
  login: async (email: string, password: string) => {
    const { data } = await http.post("/auth/login", { email, password });
    return data;
  },
  signup: async (email: string, username: string, password: string, full_name?: string) => {
    const { data } = await http.post("/auth/signup", { email, username, password, full_name });
    return data;
  },
  me: async () => {
    const { data } = await http.get("/auth/me");
    return data;
  },
};

// ─── Repositories ─────────────────────────────────────────────────────────────
export const repoApi = {
  uploadGithub: async (github_url: string, description?: string) => {
    const { data } = await http.post("/repositories/github", { github_url, description });
    return data;
  },
  uploadZip: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    const { data } = await http.post("/repositories/zip", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },
  list: async () => {
    const { data } = await http.get("/repositories");
    return data;
  },
  get: async (id: string) => {
    const { data } = await http.get(`/repositories/${id}`);
    return data;
  },
  status: async (id: string) => {
    const { data } = await http.get(`/repositories/${id}/status`);
    return data;
  },
  delete: async (id: string) => {
    await http.delete(`/repositories/${id}`);
  },
};

// ─── Chat ─────────────────────────────────────────────────────────────────────
export const chatApi = {
  createChat: async (repository_id: string, title?: string) => {
    const { data } = await http.post(`/chat/${repository_id}/chats`, { repository_id, title });
    return data;
  },
  listChats: async (repository_id: string) => {
    const { data } = await http.get(`/chat/${repository_id}/chats`);
    return data;
  },
  getMessages: async (repository_id: string, chat_id: string) => {
    const { data } = await http.get(`/chat/${repository_id}/chats/${chat_id}/messages`);
    return data;
  },
  sendMessage: async (repository_id: string, message: string, chat_id?: string) => {
    const { data } = await http.post(`/chat/${repository_id}/message`, { message, chat_id });
    return data;
  },
};

// ─── Analysis ─────────────────────────────────────────────────────────────────
export const analysisApi = {
  architecture: async (repository_id: string) => {
    const { data } = await http.post("/analyze/architecture", { repository_id });
    return data;
  },
  traceFlow: async (repository_id: string, feature: string) => {
    const { data } = await http.post("/analyze/flow", { repository_id, feature });
    return data;
  },
  investigateBug: async (repository_id: string, stack_trace: string, additional_context?: string) => {
    const { data } = await http.post("/analyze/bug", { repository_id, stack_trace, additional_context });
    return data;
  },
  documentation: async (repository_id: string) => {
    const { data } = await http.post("/analyze/documentation", { repository_id });
    return data;
  },
  onboarding: async (repository_id: string) => {
    const { data } = await http.post("/analyze/onboarding", { repository_id });
    return data;
  },
  dependencyGraph: async (repository_id: string) => {
    const { data } = await http.get(`/analyze/graph/${repository_id}`);
    return data;
  },
  search: async (repository_id: string, query: string, top_k = 10) => {
    const { data } = await http.post("/analyze/search", { repository_id, query, top_k });
    return data;
  },
};

export { extractError };
