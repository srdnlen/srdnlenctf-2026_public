function ChatHeader({ contact }) {
  return (
    <div className="header">
      <div id="info">
        <img id="chaticon" src="/images/chat-window/61.ico" alt="Chat" />
        <div id="recipient-info">
          <span id="recipient-name">{contact.name}</span>
          <span id="recipient-message">{contact.message || "Online"}</span>
        </div>
      </div>
      <div id="navbars">
        <ul className="chatnav" id="left">
          <button
            className="aerobutton chataction"
            id="action-chat-add"
          ></button>
          <button className="aerobutton chataction" id="action-share2"></button>
          <button className="aerobutton chataction" id="action-call"></button>
          <button
            className="aerobutton chataction"
            id="action-multimedia"
          ></button>
          <button className="aerobutton chataction" id="action-games"></button>
          <button className="aerobutton chataction" id="action-block"></button>
        </ul>
        <ul className="chatnav" id="right">
          <button
            className="aerobutton chataction smallarrowbtn"
            id="moreoptions"
          >
            <img
              src="/images/chat-window/1489.png"
              style={{ height: "16px" }}
              alt="Options"
            />
            <img
              className="arrowdown"
              src="/images/general/small_arrow_black.svg"
              alt="Arrow"
            />
          </button>
          <button
            className="aerobutton chataction"
            id="action-customize2"
          ></button>
        </ul>
      </div>
    </div>
  );
}

export default ChatHeader;
