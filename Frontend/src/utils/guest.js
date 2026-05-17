function generateId() {
  return Math.random().toString(36).substring(2, 10);
}

const COLORS = [
  '#FF5733', '#33FF57', '#3357FF', '#FF33A1', '#33FFF5', '#F5FF33', '#A133FF', '#FF8C33'
];

function getRandomColor() {
  return COLORS[Math.floor(Math.random() * COLORS.length)];
}

export function getGuestIdentity() {
  const stored = localStorage.getItem('flowboard_guest');
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch {
      // invalid JSON, ignore
    }
  }

  const identity = {
    id: generateId(),
    displayName: `Guest ${Math.floor(Math.random() * 1000)}`,
    color: getRandomColor(),
    avatarUrl: null,
  };

  localStorage.setItem('flowboard_guest', JSON.stringify(identity));
  return identity;
}

export function updateGuestIdentity(updates) {
  const current = getGuestIdentity();
  const updated = { ...current, ...updates };
  localStorage.setItem('flowboard_guest', JSON.stringify(updated));
  return updated;
}
