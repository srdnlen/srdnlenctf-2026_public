import { useState, useRef, useEffect } from "react";
import {
  createChat,
  getMessages,
  sendMessage,
  sendNudge as sendNudgeAPI,
  sendEmoticon as sendEmoticonAPI,
} from "./api";

export function useChatMessages(
  contactUsername,
  currentUserId,
  contactName,
  currentUsername,
) {
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    async function initChat() {
      try {
        setLoading(true);

        const { response: createResp, data: createData } =
          await createChat(contactUsername);

        if (!createResp.ok || !createData.ok) {
          throw new Error(createData.error || "Failed to create chat session");
        }

        const sid = createData.data.session_id;

        if (!isMounted) return;
        setSessionId(sid);

        const { response: msgResp, data: msgData } = await getMessages(sid);

        if (!msgResp.ok || !msgData.ok) {
          throw new Error(msgData.error || "Failed to load messages");
        }

        if (!isMounted) return;

        const transformedMessages = msgData.data.messages.map((msg) => ({
          id: msg.id,
          sender: msg.sender_id === currentUserId ? "You" : contactName,
          text: msg.body,
          timestamp: new Date(msg.created_at),
          isNudge: msg.kind === "nudge",
          kind: msg.kind,
        }));

        setMessages(transformedMessages);
        setLoading(false);
      } catch (err) {
        if (isMounted) {
          setError(err.message);
          setLoading(false);
        }
      }
    }

    initChat();

    return () => {
      isMounted = false;
    };
  }, [contactUsername, currentUserId, contactName]);

  const addMessage = (sender, text, isNudge = false, kind = "message") => {
    const newMessage = {
      sender,
      text,
      timestamp: new Date(),
      isNudge,
      kind,
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const sendMessageToServer = async (text) => {
    if (!text.trim() || !sessionId) return;

    const messageText = text;

    try {
      addMessage("You", messageText);

      const { response, data } = await sendMessage(sessionId, messageText);

      if (!response.ok || !data.ok) {
        setMessages((prev) =>
          prev.filter(
            (m) =>
              !(m.sender === "You" && m.text === messageText && m.timestamp),
          ),
        );
        addMessage(
          "System",
          `Failed to send message: ${data?.error || "Unknown error"}`,
          false,
          "error",
        );
      }
    } catch (err) {
      setMessages((prev) =>
        prev.filter((m) => !(m.sender === "You" && m.text === messageText)),
      );
      addMessage(
        "System",
        `Network error: ${err.message || "Could not send message"}`,
        false,
        "error",
      );
      console.error("Network error sending message:", err);
    }
  };

  const sendNudge = async (recipientUsername) => {
    if (!sessionId) return;

    try {
      addMessage("You", "sent a nudge!", true, "nudge");

      const { response, data } = await sendNudgeAPI(
        sessionId,
        recipientUsername,
        currentUsername,
      );

      if (!response.ok || !data.ok) {
        console.error("Nudge send failed:", data.error);
      }
    } catch (err) {
      console.error("Error sending nudge:", err);
    }
  };

  const sendEmoticon = async (recipientUsername, imageFile) => {
    if (!sessionId) return;

    try {
      const { response, data } = await sendEmoticonAPI(
        sessionId,
        recipientUsername,
        currentUsername,
        imageFile,
      );

      if (response.ok && data.ok) {
        const filename = data.data?.asset || "emoticon";
        addMessage("You", filename, false, "emoticon");
        return { success: true, filename };
      } else {
        console.error("Emoticon send failed:", data.error);
        return { success: false, error: data.error };
      }
    } catch (err) {
      console.error("Error sending emoticon:", err);
      return { success: false, error: err.message };
    }
  };

  return {
    messages,
    isTyping,
    sendMessage: sendMessageToServer,
    sendNudge,
    sendEmoticon,
    loading,
    error,
    sessionId,
  };
}

export function useAudioEffects() {
  const nudgeSoundRef = useRef(null);
  const typeSoundRef = useRef(null);

  const playNudgeSound = () => {
    if (nudgeSoundRef.current) {
      nudgeSoundRef.current.currentTime = 0;
      nudgeSoundRef.current
        .play()
        .catch((err) => console.log("Audio play failed:", err));
    }
  };

  const playTypeSound = () => {
    if (typeSoundRef.current) {
      typeSoundRef.current.currentTime = 0;
      typeSoundRef.current
        .play()
        .catch((err) => console.log("Audio play failed:", err));
    }
  };

  return {
    nudgeSoundRef,
    typeSoundRef,
    playNudgeSound,
    playTypeSound,
  };
}
