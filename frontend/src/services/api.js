// Use environment variable in production, fallback to proxy in development
const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : "/api";

// Get stored auth token
const getToken = () => localStorage.getItem("token");

// Create headers with auth token
const authHeaders = () => ({
  "Content-Type": "application/json",
  ...(getToken() && { Authorization: `Bearer ${getToken()}` }),
});

// Handle API response
const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "An error occurred" }));
    throw new Error(error.detail || "An error occurred");
  }
  return response.json();
};

// Auth API
export const authApi = {
  register: async (username, password) => {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    return handleResponse(response);
  },

  login: async (username, password) => {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    return handleResponse(response);
  },

  getMe: async () => {
    const response = await fetch(`${API_BASE}/auth/me`, {
      headers: authHeaders(),
    });
    return handleResponse(response);
  },
};

// Conversations API
export const conversationsApi = {
  list: async () => {
    const response = await fetch(`${API_BASE}/conversations`, {
      headers: authHeaders(),
    });
    return handleResponse(response);
  },

  get: async (conversationId) => {
    const response = await fetch(
      `${API_BASE}/conversations/${conversationId}`,
      {
        headers: authHeaders(),
      },
    );
    return handleResponse(response);
  },

  delete: async (conversationId) => {
    const response = await fetch(
      `${API_BASE}/conversations/${conversationId}`,
      {
        method: "DELETE",
        headers: authHeaders(),
      },
    );
    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "Failed to delete conversation" }));
      throw new Error(error.detail || "Failed to delete conversation");
    }
    return true;
  },
};

// Chat API with SSE streaming
export const chatApi = {
  sendMessage: async (message, conversationId, onEvent) => {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        message,
        conversation_id: conversationId || null,
      }),
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "An error occurred" }));
      throw new Error(error.detail || "An error occurred");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          const eventType = line.slice(7).trim();
          continue;
        }
        if (line.startsWith("data: ")) {
          const dataStr = line.slice(6);
          try {
            const data = JSON.parse(dataStr);
            // The event type is embedded in the data or inferred
            if (data.conversation_id !== undefined) {
              onEvent({ type: "conversation", data });
            } else if (data.content !== undefined) {
              onEvent({ type: "delta", data });
            } else if (data.title !== undefined) {
              onEvent({ type: "title", data });
            } else if (data.message !== undefined) {
              onEvent({ type: "error", data });
            } else if (Object.keys(data).length === 0) {
              onEvent({ type: "done", data });
            }
          } catch (e) {
            console.error("Failed to parse SSE data:", e);
          }
        }
      }
    }
  },
};
