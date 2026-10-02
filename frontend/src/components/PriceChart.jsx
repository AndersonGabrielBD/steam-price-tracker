import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function formatBRL(value) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
}

export default function PriceChart({ gameName, history }) {
  if (!history || history.length === 0) {
    return <p className="empty-state">No price history yet for this game.</p>;
  }

  const data = history.map((snapshot) => ({
    checked_at: new Date(snapshot.checked_at).toLocaleDateString("pt-BR"),
    price_brl: Number(snapshot.price_brl),
  }));

  return (
    <div className="price-chart">
      <h3>{gameName}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="checked_at" />
          <YAxis tickFormatter={formatBRL} width={90} />
          <Tooltip formatter={(value) => formatBRL(value)} />
          <Line type="stepAfter" dataKey="price_brl" stroke="#66c0f4" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
