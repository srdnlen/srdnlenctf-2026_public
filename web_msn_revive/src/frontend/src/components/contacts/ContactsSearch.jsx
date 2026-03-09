function ContactsSearch({ searchQuery, onSearchChange, onAddContact }) {
  return (
    <div className="search">
      <input
        id="contact-search"
        type="text"
        placeholder="Search contacts..."
        value={searchQuery}
        onChange={(e) => onSearchChange(e.target.value)}
      />
      <button
        className="searchbar-btn"
        id="action-friend-add"
        onClick={() => onAddContact(searchQuery)}
      ></button>
      <button className="searchbar-btn" id="action-sort"></button>
    </div>
  );
}

export default ContactsSearch;
