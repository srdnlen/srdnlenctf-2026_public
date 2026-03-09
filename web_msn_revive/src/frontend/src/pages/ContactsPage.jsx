import { useState, useMemo, useEffect } from "react";
import ContactsHeader from "../components/contacts/ContactsHeader";
import ContactsSearch from "../components/contacts/ContactsSearch";
import ContactGroup from "../components/contacts/ContactGroup";
import AlertDialog from "../components/login/AlertDialog";
import { getChatSessions, createChat } from "../utils/api";
import { useAuth } from "../contexts/AuthContext";
import "../styles/contacts.css";

function ContactsPage({ onSelectContact, onOpenSettings }) {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [chatSessions, setChatSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [alertMessage, setAlertMessage] = useState("");

  useEffect(() => {
    loadSessions();
  }, []);

  async function loadSessions() {
    try {
      setLoading(true);
      const { response, data } = await getChatSessions();

      if (!response.ok || !data.ok) {
        throw new Error(data.error || "Failed to load chat sessions");
      }

      const contacts = data.data.sessions.map((session) => ({
        id: session.with.id,
        name: session.with.username,
        status: "online",
        message: "",
        sessionId: session.session_id,
      }));

      setChatSessions(contacts);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const filteredContacts = useMemo(() => {
    if (!searchQuery) return chatSessions;

    return chatSessions.filter((contact) =>
      contact.name.toLowerCase().includes(searchQuery.toLowerCase()),
    );
  }, [searchQuery, chatSessions]);

  const handleAddContact = async (username) => {
    const trimmedUsername = username.trim();

    if (!trimmedUsername) {
      return;
    }

    try {
      const { response, data } = await createChat(trimmedUsername);

      if (!response.ok || !data.ok) {
        setAlertMessage(
          data.error_code === "INVALID_USER"
            ? "User not found or invalid username"
            : "Failed to create chat",
        );
        return;
      }

      await loadSessions();

      setSearchQuery("");
    } catch (err) {
      setAlertMessage("Network error. Please try again.");
    }
  };

  return (
    <div className="mainwindow" id="contacts">
      <ContactsHeader onOpenSettings={onOpenSettings} />

      <ContactsSearch
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onAddContact={handleAddContact}
      />

      <ul className="contact-list">
        {loading && (
          <li style={{ padding: "20px", textAlign: "center" }}>
            Loading chats...
          </li>
        )}

        {error && (
          <li style={{ padding: "20px", textAlign: "center", color: "red" }}>
            Error: {error}
          </li>
        )}

        {!loading && !error && filteredContacts.length === 0 && (
          <li style={{ padding: "20px", textAlign: "center" }}>
            {searchQuery
              ? "No contacts found"
              : "No chats yet. Start a conversation!"}
          </li>
        )}

        {!loading && !error && filteredContacts.length > 0 && (
          <ContactGroup
            title="Contacts"
            contacts={filteredContacts}
            onSelectContact={onSelectContact}
            defaultExpanded={true}
          />
        )}
      </ul>

      <AlertDialog message={alertMessage} onClose={() => setAlertMessage("")} />
    </div>
  );
}

export default ContactsPage;
