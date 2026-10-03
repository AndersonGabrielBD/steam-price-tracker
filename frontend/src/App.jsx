import { useEffect, useState } from "react";
import "./App.css";
import { addGame, connectPriceSocket, deleteGame, getGameHistory, listGames } from "./api";
import AddGameForm from "./components/AddGameForm";
import GameList from "./components/GameList";
import { IconFlame, IconGitHub, IconTag } from "./components/icons";
import PriceChart from "./components/PriceChart";

export default function App() {
  const [games, setGames] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sort, setSort] = useState("added_at");
  const [order, setOrder] = useState("desc");
  const [onSaleOnly, setOnSaleOnly] = useState(false);

  async function refreshGames() {
    const data = await listGames({ sort, order, onSaleOnly });
    setGames(data);
  }

  function handleSortChange(newSort, newOrder) {
    setSort(newSort);
    if (newOrder) setOrder(newOrder);
  }

  async function loadHistory(gameId) {
    const data = await getGameHistory(gameId);
    setHistory(data.history);
  }

  useEffect(() => {
    refreshGames().finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sort, order, onSaleOnly]);

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
    await addGame(steamAppid);
    // Re-fetch (instead of just prepending) so the new game lands in the
    // right spot for whatever sort/filter is currently active.
    await refreshGames();
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
  const onSaleCount = games.filter((g) => g.latest_price?.is_on_sale).length;
  const allTimeLowCount = games.filter((g) => g.is_all_time_low).length;

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="brand-icon" aria-hidden="true">
            <IconTag width={22} height={22} stroke="#fff" />
          </span>
          <div>
            <h1>Steam Price Tracker</h1>
            <p className="subtitle">Preços reais da Steam no Brasil (R$), atualizados ao vivo.</p>
          </div>
        </div>

        <div className="stats-bar">
          <div className="stat-pill stat-pill-purple">
            <span className="stat-icon stat-icon-purple" aria-hidden="true">
              <IconTag width={14} height={14} />
            </span>
            <span className="stat-value">{games.length}</span>
            <span className="stat-label">rastreados</span>
          </div>
          <div className="stat-pill stat-pill-coral">
            <span className="stat-icon stat-icon-coral" aria-hidden="true">
              %
            </span>
            <span className="stat-value">{onSaleCount}</span>
            <span className="stat-label">em promoção</span>
          </div>
          <div className="stat-pill stat-pill-amber">
            <span className="stat-icon stat-icon-amber" aria-hidden="true">
              <IconFlame width={14} height={14} />
            </span>
            <span className="stat-value">{allTimeLowCount}</span>
            <span className="stat-label">menor histórico</span>
          </div>
        </div>
      </header>

      <AddGameForm onAdd={handleAdd} />

      <main className={`main-layout ${selectedGame ? "has-detail" : ""}`}>
        <GameList
          games={games}
          loading={loading}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onRemove={handleRemove}
          sort={sort}
          order={order}
          onSaleOnly={onSaleOnly}
          onSortChange={handleSortChange}
          onOnSaleOnlyChange={setOnSaleOnly}
        />
        {selectedGame && (
          <PriceChart
            gameName={selectedGame.name}
            history={history}
            onClose={() => setSelectedId(null)}
          />
        )}
      </main>

      <footer className="app-footer">
        <p>Feito com FastAPI, Celery, Redis e React</p>
        <a
          className="footer-github-link"
          href="https://github.com/AndersonGabrielBD/steam-price-tracker"
          target="_blank"
          rel="noreferrer"
        >
          <IconGitHub width={16} height={16} />
          código no GitHub
        </a>
      </footer>
    </div>
  );
}
