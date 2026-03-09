import { useState, useRef } from "react";
import { EMOTICONS } from "../../utils/emoticons";

function MessageInput({ onSendMessage, onNudge, onSendEmoticon }) {
  const [inputMessage, setInputMessage] = useState("");
  const [showEmoticons, setShowEmoticons] = useState(false);
  const textareaRef = useRef(null);
  const emoticonTimeoutRef = useRef(null);
  const fileInputRef = useRef(null);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    onSendMessage(inputMessage);
    setInputMessage("");
  };

  const handleEmoticonClick = (emoticon) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const textBefore = inputMessage.substring(0, start);
    const textAfter = inputMessage.substring(end);

    const newText = textBefore + " " + emoticon.code + textAfter;
    setInputMessage(newText);
    setShowEmoticons(false);

    setTimeout(() => {
      textarea.focus();
      const newPosition = start + emoticon.code.length + 1;
      textarea.setSelectionRange(newPosition, newPosition);
    }, 0);
  };

  const handleEmoticonMouseEnter = () => {
    if (emoticonTimeoutRef.current) {
      clearTimeout(emoticonTimeoutRef.current);
    }
    setShowEmoticons(true);
  };

  const handleEmoticonMouseLeave = () => {
    emoticonTimeoutRef.current = setTimeout(() => {
      setShowEmoticons(false);
    }, 100);
  };

  const handleCustomEmoticonClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file && onSendEmoticon) {
      onSendEmoticon(file);
    }
    e.target.value = "";
  };

  return (
    <div id="send">
      <ul id="options">
        <button
          className={`aerobutton textoption smallarrowbtn dropdown-button${showEmoticons ? " active" : ""}`}
          id="emoticons-button"
          onMouseEnter={handleEmoticonMouseEnter}
          onMouseLeave={handleEmoticonMouseLeave}
        >
          <img src="/images/chat-window/412.png" alt="Emoticons" />
          <img
            className="arrowdown"
            src="/images/general/small_arrow_black.svg"
            alt="Arrow"
          />
          <div id="emoticons-menu">
            <div id="emoticons-panel">
              {EMOTICONS.map((emoticon, idx) => (
                <img
                  key={idx}
                  src={emoticon.image}
                  alt={emoticon.name}
                  title={emoticon.code}
                  onClick={() => handleEmoticonClick(emoticon)}
                  style={{ cursor: "pointer", margin: "2px" }}
                />
              ))}
            </div>
          </div>
        </button>
        <button
          className="aerobutton textoption smallarrowbtn"
          onClick={handleCustomEmoticonClick}
          title="Send custom emoticon"
        >
          <img src="/images/chat-window/1487.png" alt="Wink" />
          <img
            className="arrowdown"
            src="/images/general/small_arrow_black.svg"
            alt="Arrow"
          />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/gif"
          style={{ display: "none" }}
          onChange={handleFileSelect}
        />
        <button
          className="aerobutton textoption noarrow"
          id="nudge-button"
          onClick={onNudge}
        ></button>
        <button
          className="aerobutton textoption noarrow"
          id="audio-button"
        ></button>
        <button className="textoption separator"></button>
        <button
          className="aerobutton textoption noarrow"
          id="font-button"
        ></button>
      </ul>

      <textarea
        ref={textareaRef}
        className="chattext"
        id="write"
        placeholder="Type your message here..."
        maxLength="512"
        value={inputMessage}
        onChange={(e) => setInputMessage(e.target.value)}
        onKeyPress={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage(e);
          }
        }}
      ></textarea>

      <div id="bottomtabs">
        <button className="editortab selected" id="mode-type">
          <img src="/images/chat-window/963.png" alt="Type" />
        </button>
        <button className="editortab unselected" id="mode-draw">
          <img src="/images/chat-window/961.png" alt="Draw" />
        </button>
        <div>
          <button
            id="send-button"
            onClick={handleSendMessage}
            disabled={inputMessage.length === 0}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default MessageInput;
