import { useState } from "react";
import { searchGames } from "../api";
import { IconPlus, IconSearch } from "./icons";

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
      setError("Digite um Steam appid, ou busque pelo nome e escolha uma sugestão.");
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
        <IconSearch className="search-icon" width={16} height={16} aria-hidden="true" />
        <input
          type="text"
          placeholder="Buscar um jogo pelo nome..."
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
      <span className="or-divider">ou</span>
      <input
        type="number"
        placeholder="Steam appid"
        value={appid}
        onChange={(e) => setAppid(e.target.value)}
      />
      <button type="submit" disabled={loading}>
        {loading ? (
          "Adicionando..."
        ) : (
          <>
            <IconPlus width={15} height={15} /> Rastrear
          </>
        )}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
