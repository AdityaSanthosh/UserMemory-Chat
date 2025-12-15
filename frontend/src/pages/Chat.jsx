import Layout from "../components/Layout";
import ChatArea from "../components/ChatArea";
import { useChat } from "../hooks/useChat";

export default function Chat() {
  const {
    conversations,
    messages,
    isLoading,
    streamingContent,
    sendMessage,
    newChat,
    deleteConversation,
  } = useChat();

  return (
    <Layout
      conversations={conversations}
      onNewChat={newChat}
      onDeleteConversation={deleteConversation}
    >
      <ChatArea
        messages={messages}
        onSend={sendMessage}
        isLoading={isLoading}
        streamingContent={streamingContent}
      />
    </Layout>
  );
}
