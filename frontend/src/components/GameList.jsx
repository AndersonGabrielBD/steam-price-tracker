function formatBRL(value) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
}

export default function GameList({ games, selectedId, onSelect, onRemove }) {
  if (games.length === 0) {
    return <p className="empty-state">No games tracked yet. Add one above to get started.</p>;
  }

  return (
    <ul className="game-list">
      {games.map((game) => {
        const price = game.latest_price;
        return (
          <li
            key={game.id}
            className={game.id === selectedId ? "selected" : ""}
            onClick={() => onSelect(game.id)}
          >
            <div className="game-info">
              <span className="game-name">{game.name}</span>
              {price ? (
                <span className={price.is_on_sale ? "price on-sale" : "price"}>
                  {formatBRL(price.price_brl)}
                  {price.is_on_sale && <span className="discount">-{price.discount_percent}%</span>}
                </span>
              ) : (
                <span className="price unknown">no data yet</span>
              )}
            </div>
            <button
              className="remove-btn"
              onClick={(e) => {
                e.stopPropagation();
                onRemove(game.id);
              }}
              aria-label={`Stop tracking ${game.name}`}
            >
              x
            </button>
          </li>
        );
      })}
    </ul>
  );
}
