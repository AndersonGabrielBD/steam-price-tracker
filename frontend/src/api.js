const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_URL = API_URL.replace(/^http/, "ws") + "/ws/prices";

export async function listGames() {
  const res = await fetch(`${API_URL}/games`);
  if (!res.ok) throw new Error("Failed to load games");
  return res.json();
}

export async function addGame(steamAppid) {
  const res = await fetch(`${API_URL}/games`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ steam_appid: Number(steamAppid) }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Failed to add game");
  }
  return res.json();
}

export async function deleteGame(gameId) {
  const res = await fetch(`${API_URL}/games/${gameId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to remove game");
}

export async function getGameHistory(gameId) {
  const res = await fetch(`${API_URL}/games/${gameId}/history`);
  if (!res.ok) throw new Error("Failed to load price history");
  return res.json();
}

export async function searchGames(term) {
  const res = await fetch(`${API_URL}/games/search?q=${encodeURIComponent(term)}`);
  if (!res.ok) return [];
  return res.json();
}

export function connectPriceSocket(onPriceUpdate) {
  const socket = new WebSocket(WS_URL);
  socket.onmessage = (event) => {
    try {
      onPriceUpdate(JSON.parse(event.data));
    } catch {
      // ignore malformed payloads
    }
  };
  return socket;
}
