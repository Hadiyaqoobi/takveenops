import { useState, useEffect } from 'react';
import { getTeam } from '../api';

export default function AssigneeSelect({ value, onChange }) {
  const [members, setMembers] = useState([]);

  useEffect(() => {
    getTeam()
      .then(setMembers)
      .catch((e) => console.error('Failed to load team:', e));
  }, []);

  const humans = members.filter((m) => m.type !== 'ai-agent');
  const agents = members.filter((m) => m.type === 'ai-agent');

  return (
    <select value={value || ''} onChange={(e) => onChange(e.target.value || null)}>
      <option value="">Unassigned</option>
      {humans.length > 0 && (
        <optgroup label="Team Members">
          {humans.map((m) => (
            <option key={m.id} value={m.id}>{m.name}</option>
          ))}
        </optgroup>
      )}
      {agents.length > 0 && (
        <optgroup label="AI Agents">
          {agents.map((m) => (
            <option key={m.id} value={m.id}>{m.name}</option>
          ))}
        </optgroup>
      )}
    </select>
  );
}
