import { useState } from "react";
import { searchGames } from "../api";

export default function AddGameForm({ onAdd }) {
  const [term, setTerm] = useState("");
  const [appid, setAppid] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSearch(value) {
    setTerm(value);
    if (value.trim().length < 2) {
      setSuggestions([]);
      return;
    }
    const results = await searchGames(value);
    setSuggestions(results.slice(0, 5));
  }

  async function handleSubmit(e, overrideAppid) {
    e?.preventDefault();
    const idToAdd = overrideAppid ?? appid;
    if (!idToAdd) {
      setError("Type a Steam appid, or search by name and pick a suggestion.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await onAdd(idToAdd);
      setAppid("");
      setTerm("");
      setSuggestions([]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="add-game-form" onSubmit={handleSubmit}>
      <div className="search-box">
        <input
          type="text"
          placeholder="Search a game by name..."
          value={term}
          onChange={(e) => handleSearch(e.target.value)}
        />
        {suggestions.length > 0 && (
          <ul className="suggestions">
            {suggestions.map((game) => (
              <li key={game.appid} onClick={() => handleSubmit(null, game.appid)}>
                {game.name}
              </li>
            ))}
          </ul>
        )}
      </div>
      <span className="or-divider">or</span>
      <input
        type="number"
        placeholder="Steam appid"
        value={appid}
        onChange={(e) => setAppid(e.target.value)}
      />
      <button type="submit" disabled={loading}>
        {loading ? "Adding..." : "Track"}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
