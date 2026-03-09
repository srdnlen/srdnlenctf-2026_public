import "../styles/settings.css";
import { useAuth } from "../contexts/AuthContext";

function SettingsPage({ onClose }) {
  const { user } = useAuth();

  return (
    <div className="mainwindow" id="settings-window">
      <div className="header">
        <div className="titlebar">
          <img
            src="/images/general/live_logo.png"
            alt="MSN"
            style={{ height: "16px" }}
          />
          <span>Settings</span>
        </div>
        <div className="controls">
          <button className="aerobutton">-</button>
          <button className="aerobutton">□</button>
          <button className="aerobutton" onClick={onClose}>
            ×
          </button>
        </div>
      </div>

      <div className="settings-content">
        <h1>Work In Progress...</h1>
      </div>
    </div>
  );
}

export default SettingsPage;
