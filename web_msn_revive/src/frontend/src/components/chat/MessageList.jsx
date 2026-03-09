import { useRef, useEffect, useState } from "react";
import { EMOTICONS } from "../../utils/emoticons";

function MessageList({ messages, isTyping, contactName, sessionId }) {
  const messagesEndRef = useRef(null);
  const [emoticonUrls, setEmoticonUrls] = useState({});

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const loadEmoticons = async () => {
      for (const msg of messages) {
        if (msg.kind === "emoticon" && msg.text && !emoticonUrls[msg.text]) {
          try {
            // Fetch the emoticon image
            const response = await fetch("/api/chat/emoticons", {
              method: "POST",
              credentials: "include",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                session_id: sessionId,
                filename: msg.text,
              }),
            });

            if (response.ok) {
              const blob = await response.blob();
              const imageUrl = URL.createObjectURL(blob);
              setEmoticonUrls((prev) => ({
                ...prev,
                [msg.text]: imageUrl,
              }));
            }
          } catch (err) {
            console.error("Failed to load emoticon:", err);
          }
        }
      }
    };

    if (sessionId) {
      loadEmoticons();
    }
  }, [messages, sessionId, emoticonUrls]);

  useEffect(() => {
    return () => {
      Object.values(emoticonUrls).forEach((url) => {
        if (url.startsWith("blob:")) {
          URL.revokeObjectURL(url);
        }
      });
    };
  }, [emoticonUrls]);

  const renderMessageText = (text) => {
    let parts = [text];

    EMOTICONS.forEach((emoticon) => {
      const newParts = [];
      parts.forEach((part) => {
        if (typeof part === "string") {
          const splits = part.split(emoticon.code);
          splits.forEach((split, idx) => {
            newParts.push(split);
            if (idx < splits.length - 1) {
              newParts.push(
                <img
                  key={`${emoticon.code}-${idx}`}
                  src={emoticon.image}
                  alt={emoticon.code}
                  className="emoticon"
                  style={{ height: "19px", verticalAlign: "middle" }}
                />,
              );
            }
          });
        } else {
          newParts.push(part);
        }
      });
      parts = newParts;
    });

    return parts;
  };

  const renderMessage = (msg, index) => {
    if (msg.isNudge) {
      return (
        <span key={index} className="nudge">
          {msg.text}
        </span>
      );
    }

    if (msg.kind === "error") {
      return (
        <div key={index} style={{ margin: "4px 0" }}>
          <span
            className="sender"
            style={{ color: "#cc0000", fontWeight: "bold" }}
          >
            {msg.sender}:
          </span>
          <span
            className="message"
            style={{ color: "#cc0000", fontStyle: "italic" }}
          >
            {msg.text}
          </span>
        </div>
      );
    }

    if (msg.kind === "emoticon") {
      const isSameAsPrevious =
        index > 0 && messages[index - 1].sender === msg.sender;

      const emoticonUrl = emoticonUrls[msg.text];

      return (
        <div key={index}>
          {!isSameAsPrevious && <span className="sender">{msg.sender}:</span>}
          <span className="message">
            {emoticonUrl ? (
              <img
                src={emoticonUrl}
                alt="Custom emoticon"
                className="emoticon"
                style={{ maxHeight: "50px", verticalAlign: "middle" }}
              />
            ) : (
              <span>[Loading emoticon...]</span>
            )}
          </span>
        </div>
      );
    }

    const isSameAsPrevious =
      index > 0 && messages[index - 1].sender === msg.sender;

    return (
      <div key={index}>
        {!isSameAsPrevious && <span className="sender">{msg.sender}:</span>}
        <span className="message">{renderMessageText(msg.text)}</span>
      </div>
    );
  };

  return (
    <div id="receive">
      <div className="chattext" id="display">
        {messages.map((msg, index) => renderMessage(msg, index))}
        {isTyping && (
          <span
            className="sender"
            style={{ fontStyle: "italic", color: "#999" }}
          >
            {contactName} is typing...
          </span>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}

export default MessageList;
