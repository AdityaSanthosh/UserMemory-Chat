import Avatar from "./Avatar";
import TypingIndicator from "./TypingIndicator";
import ReactMarkdown from "react-markdown";

export default function ChatMessage({ message, isStreaming = false }) {
  const isUser = message.role === "user";
  const isError = message.role === "error";

  return (
    <div
      className={`flex gap-3 p-4 message-fade-in ${
        isUser ? "bg-base-100" : isError ? "bg-error/10" : "bg-base-200"
      }`}
    >
      <Avatar type={isUser ? "user" : "agent"} />
      <div className="flex-1 min-w-0">
        <div className="font-medium text-sm mb-1 flex items-center gap-2">
          {isUser ? "You" : "Assistant"}
          {isError && <span className="badge badge-error badge-sm">Error</span>}
        </div>
        <div
          className={`prose prose-sm max-w-none ${
            isError
              ? "text-error"
              : "prose-headings:font-bold prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-1 prose-strong:font-bold prose-code:bg-base-300 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-base-300 prose-pre:p-4 prose-pre:rounded-lg prose-blockquote:border-l-4 prose-blockquote:border-primary prose-blockquote:pl-4 prose-blockquote:italic"
          }`}
        >
          {isStreaming && !message.content ? (
            <TypingIndicator />
          ) : isError ? (
            <div className="flex items-start gap-2">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-5 h-5 flex-shrink-0 mt-0.5"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
                />
              </svg>
              <div>
                <p className="font-semibold mb-1">Request Failed</p>
                <p className="whitespace-pre-line">{message.content}</p>
              </div>
            </div>
          ) : (
            <ReactMarkdown>{message.content}</ReactMarkdown>
          )}
        </div>
      </div>
    </div>
  );
}
