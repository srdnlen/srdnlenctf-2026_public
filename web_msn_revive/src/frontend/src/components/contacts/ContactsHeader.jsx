import { useState, useEffect, useRef } from "react";
import { APP_NAME } from "../../appname";
import { useAuth } from "../../contexts/AuthContext";

function ContactsHeader({ onOpenSettings }) {
  const { user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
    };

    if (showUserMenu) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showUserMenu]);

  return (
    <>
      <div className="header">
        <div className="titlebar">
          <img
            src="/images/general/live_logo.png"
            alt="MSN"
            style={{ height: "16px" }}
          />
          <span id="appname">{APP_NAME}</span>
        </div>
        <div className="user-info">
          <img
            id="avatar"
            src="/images/chat-window/1531.png"
            alt="Profile Picture"
          />
          <img id="frame" src="/images/background/frame_48.png" alt="Frame" />
          <div className="profile">
            <div className="user-menu-wrapper" ref={menuRef}>
              <button
                className="aerobutton"
                id="user"
                onClick={() => setShowUserMenu(!showUserMenu)}
              >
                <h3 id="username">{user.username}</h3>
                <p id="status">(online)</p>
                <img
                  className="arrowdown arrowcontacts"
                  src="/images/general/small_arrow_lightblue.svg"
                  alt="Arrow"
                />
              </button>
              {showUserMenu && (
                <div className="user-dropdown-menu">
                  <button
                    className="menu-item"
                    onClick={() => {
                      setShowUserMenu(false);
                      onOpenSettings();
                    }}
                  >
                    Settings
                  </button>
                  <button
                    className="menu-item"
                    onClick={() => {
                      setShowUserMenu(false);
                      logout();
                    }}
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
            <button className="aerobutton" id="bio">
              <p style={{ margin: 0 }}>Welcome to Srdnlen CTF!</p>
              <img
                className="arrowdown arrowcontacts"
                src="/images/general/small_arrow_lightblue.svg"
                alt="Arrow"
              />
            </button>
          </div>
        </div>
      </div>

      <div id="contactsnav">
        <ul className="iconbar" id="left">
          <button
            className="aerobutton contactaction"
            id="action-mail"
          ></button>
          <button
            className="aerobutton contactaction"
            id="action-share1"
          ></button>
          <button
            className="aerobutton contactaction"
            id="action-news"
          ></button>
        </ul>
        <ul className="iconbar" id="right">
          <button
            className="aerobutton contactaction smallarrowbtn"
            id="moreoptions"
          >
            <img
              src="/images/chat-window/1489.png"
              style={{ height: "16px" }}
              alt="Options"
            />
            <img
              className="arrowdown"
              src="/images/general/small_arrow.svg"
              alt="Arrow"
            />
          </button>
          <button
            className="aerobutton contactaction"
            id="action-customize1"
          ></button>
        </ul>
      </div>
    </>
  );
}

export default ContactsHeader;
