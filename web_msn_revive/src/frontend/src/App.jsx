import { useState } from "react";
import LoginPage from "./pages/LoginPage";
import ContactsPage from "./pages/ContactsPage";
import ChatPage from "./pages/ChatPage";
import SettingsPage from "./pages/SettingsPage";
import { useAuth } from "./contexts/AuthContext";
import "./styles/defaults.css";

function App() {
  const { user, isCheckingSession } = useAuth();
  const [selectedContact, setSelectedContact] = useState(null);
  const [showSettings, setShowSettings] = useState(false);

  const handleSelectContact = (contact) => {
    setSelectedContact(contact);
  };

  const handleCloseChat = () => {
    setSelectedContact(null);
  };

  const handleOpenSettings = () => {
    setShowSettings(true);
  };

  const handleCloseSettings = () => {
    setShowSettings(false);
  };

  if (isCheckingSession) {
    return (
      <div
        className="main logon"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
        }}
      >
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <div
      className="main"
      style={{
        background: `url(/images/vista.jpg) center / cover no-repeat fixed`,
      }}
    >
      <ContactsPage
        onSelectContact={handleSelectContact}
        onOpenSettings={handleOpenSettings}
      />
      {selectedContact && (
        <ChatPage contact={selectedContact} onClose={handleCloseChat} />
      )}
      {showSettings && <SettingsPage onClose={handleCloseSettings} />}
    </div>
  );
}

export default App;
