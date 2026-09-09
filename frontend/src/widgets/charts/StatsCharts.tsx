import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const visits = Array.from({ length: 30 }, (_, i) => ({
  day: i + 1,
  visits: 20 + ((i * 7) % 35),
}));

const fund = [
  { name: 'Лимит', value: 100000 },
  { name: 'Зарезервировано', value: 25000 },
  { name: 'Потрачено', value: 45000 },
];

const funnel = [
  { stage: 'Знакомство', clients: 120 },
  { stage: 'Первый визит', clients: 80 },
  { stage: 'Регулярные', clients: 45 },
  { stage: 'Постоянные', clients: 20 },
];

export function StatsCharts() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div className="card" style={{ padding: 20 }}>
        <h3 style={{ marginTop: 0 }}>Визиты по дням (30 дней)</h3>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={visits}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Line type="monotone" dataKey="visits" stroke="#b5502a" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="card" style={{ padding: 20 }}>
        <h3 style={{ marginTop: 0 }}>Фонд клуба</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={fund}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="value" fill="#b5502a" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card" style={{ padding: 20 }}>
        <h3 style={{ marginTop: 0 }}>Воронка онбординга</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={funnel} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="stage" width={110} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="clients" fill="#7a9b76" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
