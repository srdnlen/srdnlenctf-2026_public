import { useRef, useState } from "react";
import ChatHeader from "../components/chat/ChatHeader";
import MessageList from "../components/chat/MessageList";
import MessageInput from "../components/chat/MessageInput";
import ChatAvatars from "../components/chat/ChatAvatars";
import AlertDialog from "../components/login/AlertDialog";
import { useChatMessages, useAudioEffects } from "../utils/useChatMessages";
import { useAuth } from "../contexts/AuthContext";
import "../styles/chat.css";

function ChatPage({ contact, onClose }) {
  const { user } = useAuth();
  const chatWindowRef = useRef(null);
  const [alertMessage, setAlertMessage] = useState("");
  const {
    messages,
    isTyping,
    sendMessage,
    sendNudge,
    sendEmoticon,
    loading,
    error,
    sessionId,
  } = useChatMessages(contact.name, user.id, contact.name, user.username);
  const { nudgeSoundRef, typeSoundRef, playNudgeSound, playTypeSound } =
    useAudioEffects();

  const handleSendMessage = (text) => {
    playTypeSound();
    sendMessage(text);
  };

  const handleNudge = () => {
    playNudgeSound();

    if (chatWindowRef.current) {
      chatWindowRef.current.classList.add("is-nudged");
      setTimeout(() => {
        chatWindowRef.current?.classList.remove("is-nudged");
      }, 450);
    }

    sendNudge(contact.name);
  };

  const handleSendEmoticon = async (imageFile) => {
    if (!imageFile) return;

    const validTypes = ["image/png", "image/gif", "image/jpg"];
    if (!validTypes.includes(imageFile.type)) {
      setAlertMessage("Please select a PNG, GIF, or JPG image");
      return;
    }

    const fileName = imageFile.name.toLowerCase();
    const validExtensions = [".png", ".gif", ".jpg"];
    const hasValidExtension = validExtensions.some((ext) =>
      fileName.endsWith(ext),
    );

    if (!hasValidExtension) {
      setAlertMessage("Only PNG, GIF, and JPG files are allowed");
      return;
    }

    const result = await sendEmoticon(contact.name, imageFile);
    if (!result?.success) {
      console.error("Failed to send emoticon:", result?.error);
    }
  };

  if (loading) {
    return (
      <div className="mainwindow" id="chat" ref={chatWindowRef}>
        <ChatHeader contact={contact} />
        <div className="conversation">
          <div
            id="messages"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
            }}
          >
            <p>Loading messages...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mainwindow" id="chat" ref={chatWindowRef}>
        <ChatHeader contact={contact} />
        <div className="conversation">
          <div
            id="messages"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
            }}
          >
            <p style={{ color: "red" }}>Error: {error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mainwindow" id="chat" ref={chatWindowRef}>
      <ChatHeader contact={contact} />

      <div className="conversation">
        <div id="messages">
          <MessageList
            messages={messages}
            isTyping={isTyping}
            contactName={contact.name}
            sessionId={sessionId}
          />

          <div id="handle"></div>

          <MessageInput
            onSendMessage={handleSendMessage}
            onNudge={handleNudge}
            onSendEmoticon={handleSendEmoticon}
          />
        </div>

        <ChatAvatars user={user} contact={contact} />

        <div id="expand">
          <button className="expandbutton"></button>
        </div>
      </div>

      <audio ref={nudgeSoundRef} preload="auto">
        <source src="/sounds/nudge.mp3" type="audio/mpeg" />
      </audio>
      <audio ref={typeSoundRef} preload="auto">
        <source src="/sounds/type.mp3" type="audio/mpeg" />
      </audio>

      <AlertDialog message={alertMessage} onClose={() => setAlertMessage("")} />
    </div>
  );
}

export default ChatPage;
