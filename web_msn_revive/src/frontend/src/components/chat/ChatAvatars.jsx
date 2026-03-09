function ChatAvatars({ user, contact }) {
  return (
    <div id="avatars">
      <div id="topavatar">
        <img
          className="avatar"
          src="/images/chat-window/1531.png"
          alt="Contact"
        />
        <img
          className="frame"
          src="/images/background/frame_96.png"
          alt="Frame"
        />
        <div className="avatarnav">
          <button
            className="aerobutton avataraction"
            id="action-webcam"
          ></button>
          <button className="aerobutton avataraction action-avatarmenu"></button>
        </div>
      </div>

      <div id="bottomavatar">
        <img className="avatar" src="/images/chat-window/1531.png" alt="You" />
        <img
          className="frame"
          src="/images/background/frame_96.png"
          alt="Frame"
        />
        <div className="avatarnav">
          <button className="aerobutton avataraction action-avatarmenu"></button>
        </div>
      </div>
    </div>
  );
}

export default ChatAvatars;
