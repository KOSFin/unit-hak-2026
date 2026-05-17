/**
 * Cross-tab synchronization utility for board state
 * Uses BroadcastChannel API when available, falls back to StorageEvent
 */

class CrossTabSync {
  constructor(boardId) {
    this.boardId = boardId;
    this.channel = null;
    this.listeners = new Map();
    this.init();
  }

  init() {
    try {
      // Try BroadcastChannel API first (modern browsers)
      this.channel = new BroadcastChannel(`flowboard-${this.boardId}`);
      this.channel.addEventListener('message', (event) => {
        this.handleMessage(event.data);
      });
      return;
    } catch {
      // Fallback to StorageEvent
      window.addEventListener('storage', this.handleStorageEvent);
    }
  }

  handleMessage = (data) => {
    const { type, payload } = data;
    const callbacks = this.listeners.get(type) || [];
    callbacks.forEach((cb) => cb(payload));
  };

  handleStorageEvent = (event) => {
    if (event.key?.startsWith(`flowboard-${this.boardId}:`)) {
      try {
        const data = JSON.parse(event.newValue);
        this.handleMessage(data);
      } catch {
        // Invalid data, ignore
      }
    }
  };

  send(type, payload) {
    const data = { type, payload };
    
    if (this.channel) {
      this.channel.postMessage(data);
    } else {
      // Fallback: use localStorage
      try {
        localStorage.setItem(
          `flowboard-${this.boardId}:${type}`,
          JSON.stringify(data)
        );
      } catch {
        // localStorage full or not available
      }
    }
  }

  on(type, callback) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    this.listeners.get(type).push(callback);
    
    return () => {
      const callbacks = this.listeners.get(type);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    };
  }

  off(type, callback) {
    const callbacks = this.listeners.get(type);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  dispose() {
    if (this.channel) {
      this.channel.close();
      this.channel = null;
    } else {
      window.removeEventListener('storage', this.handleStorageEvent);
    }
    this.listeners.clear();
  }
}

export function createCrossTabSync(boardId) {
  return new CrossTabSync(boardId);
}
