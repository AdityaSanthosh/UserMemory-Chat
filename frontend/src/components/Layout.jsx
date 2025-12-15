import { useState } from "react";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

export default function Layout({
  children,
  conversations = [],
  onNewChat,
  onDeleteConversation,
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-base-100">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewChat={onNewChat}
        onDeleteConversation={onDeleteConversation}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </div>
  );
}
