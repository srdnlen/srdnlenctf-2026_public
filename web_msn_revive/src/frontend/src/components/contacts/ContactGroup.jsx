import { useState } from "react";

const STATUS_ICONS = {
  online: "/images/status/online.png",
  away: "/images/status/away.png",
  busy: "/images/status/busy.png",
};

function ContactGroup({
  title,
  contacts,
  onSelectContact,
  defaultExpanded = true,
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  if (contacts.length === 0) return null;

  return (
    <>
      <button
        className="listitem headerlist"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <img
          className="arrow"
          src="/images/general/arrow_placeholder.png"
          alt="Arrow"
        />
        <b>
          {title} ({contacts.length})
        </b>
      </button>

      {isExpanded &&
        contacts.map((contact) => (
          <button
            key={contact.id}
            className="listitem contact"
            onClick={() => onSelectContact(contact)}
          >
            <img
              className="aerobutton status-icon"
              src={STATUS_ICONS[contact.status]}
              alt={contact.status}
            />
            <span className="contact-text name">{contact.name}</span>
            {contact.message && (
              <p className="contact-text message">
                &nbsp;-&nbsp;{contact.message}
              </p>
            )}
          </button>
        ))}
    </>
  );
}

export default ContactGroup;
