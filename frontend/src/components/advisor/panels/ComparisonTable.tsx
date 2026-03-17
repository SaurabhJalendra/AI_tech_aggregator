'use client';

interface ComparisonTableProps {
  data: Record<string, unknown>;
}

const DIMENSION_LABELS: Record<string, string> = {
  performance: 'Performance',
  scalability: 'Scalability',
  ease_of_use: 'Ease of Use',
  cost_efficiency: 'Cost Efficiency',
  community: 'Community',
  maturity: 'Maturity',
  flexibility: 'Flexibility',
  data_privacy: 'Data Privacy',
};

function ScoreCell({ value, best }: { value: number; best: boolean }) {
  let colorClass = 'text-gray-700 dark:text-gray-300';
  if (value >= 8) colorClass = 'text-green-600 dark:text-green-400';
  else if (value >= 6) colorClass = 'text-blue-600 dark:text-blue-400';
  else if (value <= 4) colorClass = 'text-red-600 dark:text-red-400';

  return (
    <td className={`p-3 text-center font-mono ${colorClass} ${best ? 'font-bold' : ''}`}>
      <div className="flex items-center justify-center gap-2">
        <span>{value}/10</span>
        {best && <span className="text-xs text-green-500">&#9733;</span>}
      </div>
      <div className="mt-1 h-1.5 w-full rounded-full bg-gray-200 dark:bg-gray-700">
        <div
          className={`h-1.5 rounded-full ${
            value >= 8
              ? 'bg-green-500'
              : value >= 6
                ? 'bg-blue-500'
                : value >= 4
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
          }`}
          style={{ width: `${value * 10}%` }}
        />
      </div>
    </td>
  );
}

export default function ComparisonTable({ data }: ComparisonTableProps) {
  const comparison = data.comparison as Record<string, unknown> | undefined;

  if (!comparison) {
    return (
      <div className="flex h-64 items-center justify-center p-6">
        <p className="text-gray-500">No comparison data available</p>
      </div>
    );
  }

  const modules = (comparison.modules as string[]) || [];
  const dimensions = (comparison.dimensions as string[]) || [];
  const matrix = (comparison.matrix as Record<string, Record<string, { value: number }>>) || {};
  const highlights = (comparison.highlights as Record<string, string[]>) || {};
  const recommendation = (comparison.recommendation as string) || '';

  return (
    <div className="p-6">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b-2 border-gray-200 dark:border-gray-700">
              <th className="p-3 text-left font-semibold text-gray-500">Dimension</th>
              {modules.map((mod) => (
                <th key={mod} className="p-3 text-center font-semibold">
                  {mod.replace(/_/g, ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dimensions.map((dim) => {
              const scores = modules.map((mod) => {
                const score = matrix[mod]?.[dim];
                return typeof score === 'object' && score?.value != null
                  ? score.value
                  : typeof score === 'number'
                    ? score
                    : 5;
              });
              const maxScore = Math.max(...scores);

              return (
                <tr
                  key={dim}
                  className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900/50"
                >
                  <td className="p-3 font-medium text-gray-600 dark:text-gray-400">
                    {DIMENSION_LABELS[dim] || dim.replace(/_/g, ' ')}
                  </td>
                  {modules.map((mod, i) => (
                    <ScoreCell
                      key={`${mod}-${dim}`}
                      value={scores[i]}
                      best={scores[i] === maxScore && maxScore > 5}
                    />
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Highlights */}
      {Object.keys(highlights).length > 0 && (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {modules.map((mod) => {
            const modHighlights = highlights[mod] || [];
            if (modHighlights.length === 0) return null;
            return (
              <div
                key={mod}
                className="rounded-lg border border-gray-200 p-4 dark:border-gray-700"
              >
                <h3 className="mb-2 text-sm font-semibold">
                  {mod.replace(/_/g, ' ')} Strengths
                </h3>
                <ul className="space-y-1">
                  {modHighlights.map((h, i) => (
                    <li key={i} className="text-xs text-gray-600 dark:text-gray-400">
                      {h}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      )}

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
