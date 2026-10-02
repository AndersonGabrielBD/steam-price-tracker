import { useEffect, useState } from "react";
import "./App.css";
import { addGame, connectPriceSocket, deleteGame, getGameHistory, listGames } from "./api";
import AddGameForm from "./components/AddGameForm";
import GameList from "./components/GameList";
import PriceChart from "./components/PriceChart";

export default function App() {
  const [games, setGames] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  async function refreshGames() {
    const data = await listGames();
    setGames(data);
  }

  async function loadHistory(gameId) {
    const data = await getGameHistory(gameId);
    setHistory(data.history);
  }

  useEffect(() => {
    refreshGames().finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selectedId) loadHistory(selectedId);
  }, [selectedId]);

  // Live updates: when a background price check detects a change, the
  // server pushes it here immediately -- no polling, no page refresh.
  useEffect(() => {
    const socket = connectPriceSocket((event) => {
      setGames((current) =>
        current.map((game) =>
          game.id === event.game_id
            ? {
                ...game,
                latest_price: {
                  price_brl: event.price_brl,
                  discount_percent: event.discount_percent,
                  is_on_sale: event.is_on_sale,
                  checked_at: event.checked_at,
                },
              }
            : game
        )
      );
      setHistory((current) => {
        if (!selectedId || event.game_id !== selectedId) return current;
        return [...current, { ...event }];
      });
    });
    return () => socket.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  async function handleAdd(steamAppid) {
    const game = await addGame(steamAppid);
    setGames((current) => [game, ...current]);
  }

  async function handleRemove(gameId) {
    await deleteGame(gameId);
    setGames((current) => current.filter((g) => g.id !== gameId));
    if (selectedId === gameId) {
      setSelectedId(null);
      setHistory([]);
    }
  }

  const selectedGame = games.find((g) => g.id === selectedId);

  return (
    <div className="app">
      <header>
        <h1>Steam Price Tracker</h1>
        <p className="subtitle">Preços reais da Steam no Brasil (R$), atualizados ao vivo.</p>
      </header>

      <AddGameForm onAdd={handleAdd} />

      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="layout">
          <GameList games={games} selectedId={selectedId} onSelect={setSelectedId} onRemove={handleRemove} />
          {selectedGame && <PriceChart gameName={selectedGame.name} history={history} />}
        </div>
      )}
    </div>
  );
}
