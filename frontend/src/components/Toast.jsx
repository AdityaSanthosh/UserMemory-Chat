import {
  useState,
  useEffect,
  createContext,
  useContext,
  useCallback,
} from "react";

const ToastContext = createContext(null);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = "info", duration = 5000) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);

    if (duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, duration);
    }

    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = {
    info: (message, duration) => addToast(message, "info", duration),
    success: (message, duration) => addToast(message, "success", duration),
    warning: (message, duration) => addToast(message, "warning", duration),
    error: (message, duration) => addToast(message, "error", duration),
    remove: removeToast,
  };

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="toast toast-end toast-top z-50">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`alert shadow-lg ${
              t.type === "error"
                ? "alert-error"
                : t.type === "success"
                  ? "alert-success"
                  : t.type === "warning"
                    ? "alert-warning"
                    : "alert-info"
            } cursor-pointer transition-all`}
            onClick={() => removeToast(t.id)}
          >
            <span className="whitespace-pre-line">{t.message}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
