import { useState, useCallback, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { conversationsApi, chatApi } from "../services/api";
import { useToast } from "../components/Toast";

// LocalStorage key for error persistence
const ERROR_STORAGE_KEY = "chat_errors";

// Get stored errors (returns object with conversationId as keys)
const getStoredErrors = () => {
  try {
    const stored = localStorage.getItem(ERROR_STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch (e) {
    console.error("Failed to parse stored errors:", e);
    return {};
  }
};

// Store error for a specific conversation
const storeError = (conversationId, errorContent) => {
  const errors = getStoredErrors();
  errors[conversationId] = {
    content: errorContent,
    timestamp: Date.now(),
  };
  localStorage.setItem(ERROR_STORAGE_KEY, JSON.stringify(errors));
};

// Remove error for a specific conversation
const removeError = (conversationId) => {
  const errors = getStoredErrors();
  delete errors[conversationId];
  localStorage.setItem(ERROR_STORAGE_KEY, JSON.stringify(errors));
};

// Get error for a specific conversation
const getErrorForConversation = (conversationId) => {
  const errors = getStoredErrors();
  return errors[conversationId]?.content || null;
};

export function useChat() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();

  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [currentConversationId, setCurrentConversationId] = useState(
    conversationId || null,
  );

  // Load conversations list
  const loadConversations = useCallback(async () => {
    try {
      const data = await conversationsApi.list();
      setConversations(data || []);
    } catch (err) {
      toast.error("Failed to load conversations");
    }
  }, [toast]);

  // Load conversation messages
  const loadConversation = useCallback(
    async (id) => {
      if (!id) {
        setMessages([]);
        setCurrentConversationId(null);
        return;
      }

      try {
        const data = await conversationsApi.get(id);
        const loadedMessages = data.messages || [];

        // Check if there's a stored error for this conversation
        const storedError = getErrorForConversation(id);
        if (storedError) {
          setMessages([
            ...loadedMessages,
            {
              role: "error",
              content: storedError,
            },
          ]);
        } else {
          setMessages(loadedMessages);
        }

        setCurrentConversationId(id);
      } catch (err) {
        toast.error("Failed to load conversation");
        navigate("/");
      }
    },
    [toast, navigate],
  );

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Load conversation when URL changes
  useEffect(() => {
    if (conversationId) {
      loadConversation(conversationId);
    } else {
      setMessages([]);
      setCurrentConversationId(null);
    }
  }, [conversationId, loadConversation]);

  // Send message
  const sendMessage = useCallback(
    async (content) => {
      if (isLoading) return;

      // Add user message to UI immediately
      const userMessage = { role: "user", content };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setStreamingContent("");

      let newConversationId = currentConversationId;
      let accumulatedContent = "";

      try {
        await chatApi.sendMessage(content, currentConversationId, (event) => {
          switch (event.type) {
            case "conversation":
              newConversationId = event.data.conversation_id;
              setCurrentConversationId(newConversationId);
              if (event.data.is_new) {
                // Navigate to new conversation URL without full reload
                navigate(`/chat/${newConversationId}`, { replace: true });
              }
              break;

            case "delta":
              accumulatedContent += event.data.content;
              setStreamingContent(accumulatedContent);
              break;

            case "title":
              // Update conversation in sidebar
              setConversations((prev) => {
                const exists = prev.some((c) => c.id === newConversationId);
                if (exists) {
                  return prev.map((c) =>
                    c.id === newConversationId
                      ? { ...c, title: event.data.title }
                      : c,
                  );
                }
                return [
                  { id: newConversationId, title: event.data.title },
                  ...prev,
                ];
              });
              break;

            case "done":
              // Add assistant message to messages
              if (accumulatedContent) {
                setMessages((prev) => [
                  ...prev,
                  { role: "model", content: accumulatedContent },
                ]);

                // Clear any stored error for this conversation on successful message
                if (newConversationId) {
                  removeError(newConversationId);
                }
              }
              setStreamingContent("");
              setIsLoading(false);
              break;

            case "error":
              // Streaming error - display as error message in chat
              const errorMessage = event.data.message || "An error occurred";

              // Check if it's a credits/limit error and customize the message
              let displayMessage = errorMessage;
              if (
                errorMessage.toLowerCase().includes("credit") ||
                errorMessage.toLowerCase().includes("limit") ||
                errorMessage.toLowerCase().includes("quota") ||
                errorMessage.toLowerCase().includes("rate limit")
              ) {
                displayMessage = `⚠️ Credits Limit Reached\n\n${errorMessage}`;
              }

              // Store error in localStorage for this conversation
              if (newConversationId) {
                storeError(newConversationId, displayMessage);
              }

              // Add error message to chat as assistant error message
              setMessages((prev) => [
                ...prev,
                {
                  role: "error",
                  content: displayMessage,
                },
              ]);
              setStreamingContent("");
              setIsLoading(false);
              break;
          }
        });
      } catch (err) {
        // HTTP error (non-200 status) - show error banner/toast
        const errorMessage = err.message || "Failed to send message";
        toast.error(errorMessage, 7000); // Show for 7 seconds

        setIsLoading(false);
        setStreamingContent("");
        // Remove the user message if the request failed completely
        setMessages((prev) => prev.slice(0, -1));
      }
    },
    [isLoading, currentConversationId, navigate, toast],
  );

  // Start new chat
  const newChat = useCallback(() => {
    setMessages([]);
    setCurrentConversationId(null);
    setStreamingContent("");
    // DO NOT clear errors - they belong to their specific conversations
  }, []);

  // Delete conversation
  const deleteConversation = useCallback(
    async (conversationId) => {
      try {
        await conversationsApi.delete(conversationId);

        // Remove from conversations list
        setConversations((prev) => prev.filter((c) => c.id !== conversationId));

        // Clear error for this conversation from localStorage
        removeError(conversationId);

        // If deleting current conversation, navigate to home
        if (currentConversationId === conversationId) {
          navigate("/");
          setMessages([]);
          setCurrentConversationId(null);
        }

        toast.success("Conversation deleted");
        return true;
      } catch (err) {
        toast.error(err.message || "Failed to delete conversation");
        return false;
      }
    },
    [currentConversationId, navigate, toast],
  );

  return {
    conversations,
    messages,
    isLoading,
    streamingContent,
    currentConversationId,
    sendMessage,
    newChat,
    loadConversations,
    deleteConversation,
  };
}
