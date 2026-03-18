import { useState, useRef, useEffect } from 'react';
import { getTeam } from '../api';

export default function MentionInput({ value, onChange, onSubmit, placeholder, disabled }) {
  const [showDropdown, setShowDropdown] = useState(false);
  const [members, setMembers] = useState([]);
  const [query, setQuery] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    getTeam().then(setMembers).catch(() => {});
  }, []);

  const handleChange = (e) => {
    const text = e.target.value;
    onChange(text);

    const cursorPos = e.target.selectionStart;
    const before = text.slice(0, cursorPos);
    const match = before.match(/@(\w*)$/);
    if (match) {
      setQuery(match[1].toLowerCase());
      setShowDropdown(true);
    } else {
      setShowDropdown(false);
    }
  };

  const handleSelect = (memberId) => {
    const cursorPos = inputRef.current.selectionStart;
    const before = value.slice(0, cursorPos);
    const after = value.slice(cursorPos);
    const replaced = before.replace(/@\w*$/, `@${memberId} `);
    onChange(replaced + after);
    setShowDropdown(false);
    inputRef.current.focus();
  };

  const filtered = members.filter(
    (m) => m.id.toLowerCase().includes(query) || m.name.toLowerCase().includes(query)
  );

  return (
    <div className="mention-input-wrap">
      <input
        ref={inputRef}
        className="comment-input"
        value={value}
        onChange={handleChange}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !showDropdown) onSubmit?.();
          if (e.key === 'Escape') setShowDropdown(false);
        }}
        placeholder={placeholder}
        disabled={disabled}
      />
      {showDropdown && filtered.length > 0 && (
        <div className="mention-dropdown">
          {filtered.map((m) => (
            <button key={m.id} className="mention-option" onClick={() => handleSelect(m.id)}>
              <span className="mention-name">{m.name}</span>
              <span className="mention-id">@{m.id}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
