import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

export default function Sidebar({
  conversations,
  isOpen,
  onClose,
  onNewChat,
  onDeleteConversation,
}) {
  const navigate = useNavigate();
  const { conversationId } = useParams();
  const [deletingId, setDeletingId] = useState(null);
  const [hoveredId, setHoveredId] = useState(null);

  const handleConversationClick = (id) => {
    navigate(`/chat/${id}`);
    onClose?.();
  };

  const handleNewChat = () => {
    onNewChat?.();
    navigate("/");
    onClose?.();
  };

  const handleDeleteClick = (e, id) => {
    e.stopPropagation();
    setDeletingId(id);
  };

  const confirmDelete = async () => {
    if (deletingId && onDeleteConversation) {
      await onDeleteConversation(deletingId);
      setDeletingId(null);
    }
  };

  const cancelDelete = () => {
    setDeletingId(null);
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-72 bg-base-200 transform transition-transform duration-200 ease-in-out lg:transform-none ${
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        } flex flex-col h-full`}
      >
        {/* Header */}
        <div className="p-4 border-b border-base-300">
          <button
            onClick={handleNewChat}
            className="btn btn-primary w-full gap-2"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-5 h-5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 4.5v15m7.5-7.5h-15"
              />
            </svg>
            New Chat
          </button>
        </div>

        {/* Conversations list */}
        <div className="flex-1 overflow-y-auto p-2">
          {conversations.length === 0 ? (
            <p className="text-sm text-base-content/60 p-2 text-center">
              No conversations yet
            </p>
          ) : (
            <ul className="menu menu-sm gap-1">
              {conversations.map((conversation) => (
                <li
                  key={conversation.id}
                  onMouseEnter={() => setHoveredId(conversation.id)}
                  onMouseLeave={() => setHoveredId(null)}
                >
                  <div
                    className={`flex items-center gap-2 pr-1 rounded-lg transition-colors ${
                      conversationId === conversation.id
                        ? "bg-primary/10 text-primary font-medium"
                        : "hover:bg-base-300"
                    }`}
                  >
                    <button
                      onClick={() => handleConversationClick(conversation.id)}
                      className="flex-1 flex items-center gap-2 min-w-0 hover:bg-transparent pr-2"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={1.5}
                        stroke="currentColor"
                        className={`w-4 h-4 shrink-0 ${
                          conversationId === conversation.id
                            ? "text-primary"
                            : ""
                        }`}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z"
                        />
                      </svg>
                      <span className="truncate block overflow-hidden text-ellipsis whitespace-nowrap">
                        {(conversation.title || "Untitled").length > 30
                          ? (conversation.title || "Untitled").substring(
                              0,
                              30,
                            ) + "..."
                          : conversation.title || "Untitled"}
                      </span>
                    </button>
                    {/* Delete button - only visible on hover */}
                    {hoveredId === conversation.id && (
                      <button
                        onClick={(e) => handleDeleteClick(e, conversation.id)}
                        className="btn btn-ghost btn-xs btn-square shrink-0 text-error hover:bg-error/10"
                        aria-label="Delete conversation"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          strokeWidth={1.5}
                          stroke="currentColor"
                          className="w-4 h-4"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
                          />
                        </svg>
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      {/* Delete Confirmation Modal */}
      {deletingId && (
        <div className="fixed inset-0 bg-black/50 z-[60] flex items-center justify-center p-4">
          <div className="bg-base-100 rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-bold mb-2">Delete Conversation?</h3>
            <p className="text-base-content/70 mb-6">
              This will permanently delete this conversation and all its
              messages. This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button onClick={cancelDelete} className="btn btn-ghost">
                Cancel
              </button>
              <button onClick={confirmDelete} className="btn btn-error">
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
