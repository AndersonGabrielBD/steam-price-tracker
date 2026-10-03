import { IconChevronDown, IconChevronUp, IconClose, IconFlame, IconGamepad } from "./icons";

function formatBRL(value) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
}

const SORT_OPTIONS = [
  { value: "added_at", label: "Adicionado recentemente" },
  { value: "discount", label: "Maior desconto" },
  { value: "price", label: "Menor preço" },
  { value: "name", label: "Nome" },
];

function GameGridSkeleton() {
  return (
    <div className="game-grid">
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="skeleton-card">
          <div className="skeleton-cover" />
          <div className="skeleton-body">
            <div className="skeleton-line skeleton-line-title" />
            <div className="skeleton-line skeleton-line-price" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function GameList({
  games,
  loading,
  selectedId,
  onSelect,
  onRemove,
  sort,
  order,
  onSaleOnly,
  onSortChange,
  onOnSaleOnlyChange,
}) {
  return (
    <div className="game-list-panel">
      <div className="game-list-controls">
        <select
          className="sort-select"
          value={sort}
          onChange={(e) => onSortChange(e.target.value)}
          aria-label="Ordenar por"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          className="order-toggle"
          onClick={() => onSortChange(sort, order === "asc" ? "desc" : "asc")}
          aria-label={order === "asc" ? "Crescente" : "Decrescente"}
          title={order === "asc" ? "Crescente" : "Decrescente"}
        >
          {order === "asc" ? <IconChevronUp width={14} height={14} /> : <IconChevronDown width={14} height={14} />}
        </button>
        <label className="on-sale-filter">
          <input
            type="checkbox"
            checked={onSaleOnly}
            onChange={(e) => onOnSaleOnlyChange(e.target.checked)}
          />
          Só em promoção
        </label>
      </div>

      {loading ? (
        <GameGridSkeleton />
      ) : (
        <div className="game-grid">
          {games.length === 0 ? (
            <div className="empty-state">
              <span className="empty-state-icon" aria-hidden="true">
                <IconGamepad width={32} height={32} />
              </span>
              <p>Nenhum jogo rastreado ainda.</p>
              <p className="empty-state-hint">Busque um jogo acima para começar a acompanhar o preço.</p>
            </div>
          ) : (
            games.map((game) => {
              const price = game.latest_price;
              return (
                <article
                  key={game.id}
                  className={`game-card ${game.id === selectedId ? "selected" : ""}`}
                  onClick={() => onSelect(game.id)}
                >
                  <div className="game-card-cover">
                    {game.header_image_url ? (
                      <img className="game-cover" src={game.header_image_url} alt="" />
                    ) : (
                      <div className="game-cover-placeholder" aria-hidden="true" />
                    )}
                    {price?.is_on_sale && <span className="discount-tag">-{price.discount_percent}%</span>}
                    {game.is_all_time_low && (
                      <span className="all-time-low-tag">
                        <IconFlame width={12} height={12} /> Menor histórico
                      </span>
                    )}
                    <button
                      className="remove-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemove(game.id);
                      }}
                      aria-label={`Parar de rastrear ${game.name}`}
                    >
                      <IconClose width={13} height={13} />
                    </button>
                  </div>
                  <div className="game-card-body">
                    <span className="game-name">{game.name}</span>
                    {price ? (
                      <span className={price.is_on_sale ? "price on-sale" : "price"}>
                        {formatBRL(price.price_brl)}
                      </span>
                    ) : (
                      <span className="price unknown">sem dado ainda</span>
                    )}
                  </div>
                </article>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
