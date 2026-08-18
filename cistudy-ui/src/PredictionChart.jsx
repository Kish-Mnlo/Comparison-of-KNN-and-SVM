import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const toValue = (label) => {
  if (label === 'Higher') return 1;
  if (label === 'Lower') return 0;
  return null;
};

function buildChartData(predictionHistory) {
  return [...predictionHistory]
    .sort((a, b) => (a.date > b.date ? 1 : a.date < b.date ? -1 : 0))
    .map((item) => ({
      date: item.date,
      Actual: toValue(item.actual),
      KNN: toValue(item.knnPrediction),
      SVM: toValue(item.svmPrediction),
    }));
}

function computeAccuracy(predictionHistory, key) {
  const resolved = predictionHistory.filter(
    (item) => item.actual && item.actual !== 'Pending'
  );
  if (resolved.length === 0) return null;
  const correct = resolved.filter((item) => item[key] === item.actual).length;
  return Math.round((correct / resolved.length) * 100);
}

const yTickFormatter = (value) => {
  if (value === 1) return 'Higher';
  if (value === 0) return 'Lower';
  return '';
};

const tooltipFormatter = (value) => {
  if (value === 1) return 'Higher';
  if (value === 0) return 'Lower';
  return 'Pending';
};

export default function PredictionChart({ predictionHistory }) {
  if (predictionHistory.length === 0) {
    return (
      <div className="pr-warning">
        Prediction chart will show here once you have search history.
      </div>
    );
  }

  const chartData = buildChartData(predictionHistory);
  const knnAccuracy = computeAccuracy(predictionHistory, 'knnPrediction');
  const svmAccuracy = computeAccuracy(predictionHistory, 'svmPrediction');

  return (
    <div className="chart-card">
      <div className="chart-accuracy-row">
        <div className="chart-accuracy-pill">
          KNN Accuracy: {knnAccuracy === null ? '—' : `${knnAccuracy}%`}
        </div>
        <div className="chart-accuracy-pill">
          SVM Accuracy: {svmAccuracy === null ? '—' : `${svmAccuracy}%`}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(150,150,150,0.25)" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis
            domain={[-0.2, 1.2]}
            ticks={[0, 1]}
            tickFormatter={yTickFormatter}
            tick={{ fontSize: 12 }}
          />
          <Tooltip formatter={tooltipFormatter} />
          <Legend />
          <Line
            type="stepAfter"
            dataKey="Actual"
            stroke="#1f9d55"
            strokeWidth={3}
            dot={{ r: 4 }}
            connectNulls={false}
          />
          <Line
            type="stepAfter"
            dataKey="KNN"
            stroke="#2563eb"
            strokeWidth={2}
            strokeDasharray="4 3"
            dot={{ r: 3 }}
          />
          <Line
            type="stepAfter"
            dataKey="SVM"
            stroke="#dc2626"
            strokeWidth={2}
            strokeDasharray="4 3"
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}