'use client';

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

interface ComparisonChartProps {
  data: Record<string, unknown>;
}

const COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6'];

const DIMENSION_LABELS: Record<string, string> = {
  performance: 'Performance',
  scalability: 'Scalability',
  ease_of_use: 'Ease of Use',
  cost_efficiency: 'Cost',
  community: 'Community',
  maturity: 'Maturity',
  flexibility: 'Flexibility',
  data_privacy: 'Privacy',
};

export default function ComparisonChart({ data }: ComparisonChartProps) {
  const comparison = data.comparison as Record<string, unknown> | undefined;
  const chartType = (data.chart_type as string) || 'radar';

  if (!comparison) {
    return (
      <div className="flex h-96 items-center justify-center p-6">
        <p className="text-gray-500">No comparison data available</p>
      </div>
    );
  }

  const modules = (comparison.modules as string[]) || [];
  const dimensions = (comparison.dimensions as string[]) || [];
  const matrix = (comparison.matrix as Record<string, Record<string, { value: number }>>) || {};
  const recommendation = (comparison.recommendation as string) || '';
  const overallRanking = (comparison.overall_ranking as string[]) || [];

  // Build chart data
  const chartData = dimensions.map((dim) => {
    const row: Record<string, string | number> = {
      dimension: DIMENSION_LABELS[dim] || dim.replace(/_/g, ' '),
    };
    modules.forEach((mod) => {
      const score = matrix[mod]?.[dim];
      row[mod] = typeof score === 'object' && score?.value != null ? score.value : (typeof score === 'number' ? score : 5);
    });
    return row;
  });

  return (
    <div className="p-6">
      {/* Rankings summary */}
      {overallRanking.length > 0 && (
        <div className="mb-6 flex items-center gap-3">
          <span className="text-sm font-medium text-gray-500">Ranking:</span>
          {overallRanking.map((slug, i) => (
            <span
              key={slug}
              className="inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm font-medium"
              style={{
                backgroundColor: `${COLORS[i % COLORS.length]}15`,
                color: COLORS[i % COLORS.length],
              }}
            >
              #{i + 1} {slug.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}

      {/* Chart */}
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'bar' ? (
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="dimension" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 10]} />
              <Tooltip />
              <Legend />
              {modules.map((mod, i) => (
                <Bar
                  key={mod}
                  dataKey={mod}
                  fill={COLORS[i % COLORS.length]}
                  name={mod.replace(/_/g, ' ')}
                />
              ))}
            </BarChart>
          ) : (
            <RadarChart data={chartData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11 }} />
              <PolarRadiusAxis angle={90} domain={[0, 10]} tick={{ fontSize: 10 }} />
              {modules.map((mod, i) => (
                <Radar
                  key={mod}
                  name={mod.replace(/_/g, ' ')}
                  dataKey={mod}
                  stroke={COLORS[i % COLORS.length]}
                  fill={COLORS[i % COLORS.length]}
                  fillOpacity={0.15}
                  strokeWidth={2}
                />
              ))}
              <Legend />
              <Tooltip />
            </RadarChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Recommendation */}
      {recommendation && (
        <div className="mt-6 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-950">
          <h3 className="mb-1 text-sm font-semibold text-blue-800 dark:text-blue-300">
            Recommendation
          </h3>
          <p className="text-sm text-blue-700 dark:text-blue-400">{recommendation}</p>
        </div>
      )}
    </div>
  );
}
