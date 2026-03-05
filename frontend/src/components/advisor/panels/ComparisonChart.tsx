'use client';

interface ComparisonChartProps {
  data: Record<string, unknown>;
}

/**
 * ComparisonChart renders a radar or bar chart comparing modules across
 * dimensions using Recharts. Placeholder implementation.
 */
export default function ComparisonChart({ data }: ComparisonChartProps) {
  const modules = (data.modules as string[]) || [];
  const chartType = (data.chart_type as string) || 'radar';

  return (
    <div className="p-6">
      <h2 className="mb-4 text-xl font-semibold">Comparison Chart</h2>

      <div className="flex h-96 items-center justify-center rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700">
        <div className="text-center">
          <p className="text-gray-500">
            {chartType.charAt(0).toUpperCase() + chartType.slice(1)} chart
            will render here
          </p>
          <p className="mt-2 text-sm text-gray-400">
            Powered by Recharts
          </p>
          {modules.length > 0 && (
            <p className="mt-2 text-xs text-gray-400">
              Comparing: {modules.join(', ')}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
