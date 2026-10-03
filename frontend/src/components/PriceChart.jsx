import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { IconClose, IconTrendingUp } from "./icons";

function formatBRL(value) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
}

function CustomDot({ cx, cy, payload }) {
  const isBackfill = payload.source === "itad_backfill";
  return (
    <circle
      cx={cx}
      cy={cy}
      r={3}
      fill={isBackfill ? "#65667d" : "#8b5cf6"}
      stroke="#121420"
      strokeWidth={1}
    />
  );
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const point = payload[0].payload;
  const pctVsInitial =
    point.initial_price_brl > 0
      ? Math.round((1 - point.price_brl / point.initial_price_brl) * 100)
      : 0;
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip-date">{label}</p>
      <p className="chart-tooltip-price">{formatBRL(point.price_brl)}</p>
      {pctVsInitial > 0 && <p className="chart-tooltip-discount">-{pctVsInitial}% vs. preço cheio</p>}
      {point.source === "itad_backfill" && (
        <p className="chart-tooltip-source">histórico via IsThereAnyDeal</p>
      )}
    </div>
  );
}

export default function PriceChart({ gameName, history, onClose }) {
  if (!history || history.length === 0) {
    return (
      <div className="detail-panel">
        <div className="detail-panel-header">
          <h3>{gameName}</h3>
          <button className="detail-close-btn" onClick={onClose} aria-label="Fechar detalhe">
            <IconClose width={13} height={13} />
          </button>
        </div>
        <div className="price-chart empty-state">
          <span className="empty-state-icon" aria-hidden="true">
            <IconTrendingUp width={32} height={32} />
          </span>
          <p>Ainda não há histórico de preço para este jogo.</p>
        </div>
      </div>
    );
  }

  const data = history.map((snapshot) => ({
    checked_at: new Date(snapshot.checked_at).toLocaleDateString("pt-BR"),
    price_brl: Number(snapshot.price_brl),
    initial_price_brl: Number(snapshot.initial_price_brl ?? snapshot.price_brl),
    source: snapshot.source,
  }));

  const minPrice = Math.min(...data.map((d) => d.price_brl));
  const minPoint = data.find((d) => d.price_brl === minPrice);

  return (
    <div className="detail-panel">
      <div className="detail-panel-header">
        <h3>{gameName}</h3>
        <button className="detail-close-btn" onClick={onClose} aria-label="Fechar detalhe">
          ×
        </button>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.45} />
              <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2c40" />
          <XAxis dataKey="checked_at" stroke="#65667d" />
          <YAxis tickFormatter={formatBRL} width={90} stroke="#65667d" />
          <Tooltip content={<ChartTooltip />} />
          <Area
            type="stepAfter"
            dataKey="price_brl"
            stroke="#8b5cf6"
            strokeWidth={2}
            fill="url(#priceGradient)"
            dot={<CustomDot />}
            isAnimationActive={false}
          />
          {minPoint && (
            <ReferenceDot
              x={minPoint.checked_at}
              y={minPoint.price_brl}
              r={6}
              fill="#4ade80"
              stroke="#0c0d14"
              label={{ value: "menor preço", position: "top", fill: "#4ade80", fontSize: 11 }}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
      <p className="chart-legend">
        <span className="legend-dot legend-dot-live" /> checagem ao vivo (Steam)
        <span className="legend-dot legend-dot-backfill" /> histórico (IsThereAnyDeal)
      </p>
    </div>
  );
}
