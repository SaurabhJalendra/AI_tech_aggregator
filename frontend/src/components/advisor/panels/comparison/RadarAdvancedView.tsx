'use client';

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import {
  DIMENSION_LABELS,
  getMatrixScore,
  type ParsedComparison,
} from '@/lib/comparisonPanel';
import { formatEntityLabel, getEntityColor } from '@/lib/entityColors';

interface RadarAdvancedViewProps {
  comparison: ParsedComparison;
}

export default function RadarAdvancedView({ comparison }: RadarAdvancedViewProps) {
  const displayOrder = comparison.pipelineRanking;
  const chartData = comparison.dimensions.map((dim) => {
    const row: Record<string, string | number> = {
      dimension: DIMENSION_LABELS[dim] || dim.replace(/_/g, ' '),
    };
    displayOrder.forEach((mod) => {
      row[mod] = getMatrixScore(comparison.matrix, mod, dim).value;
    });
    return row;
  });

  return (
    <div className="surface-muted h-80 rounded-xl border-dashed p-2">
      <p className="mb-2 text-center text-[10px] text-[var(--text-muted)]">Advanced radar view</p>
      <div className="mb-2 flex flex-wrap justify-center gap-3">
        {displayOrder.map((mod, i) => (
          <span
            key={mod}
            className="flex items-center gap-1.5 text-[10px] font-medium"
            style={{ color: getEntityColor(mod) }}
          >
            <span
              className="inline-block h-2 w-2 rounded-sm"
              style={{ backgroundColor: getEntityColor(mod) }}
            />
            #{i + 1} {formatEntityLabel(mod)}
          </span>
        ))}
      </div>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={chartData}>
          <PolarGrid />
          <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 10 }} />
          <PolarRadiusAxis angle={90} domain={[0, 10]} tick={{ fontSize: 9 }} />
          {displayOrder.map((mod) => (
            <Radar
              key={mod}
              name={formatEntityLabel(mod)}
              dataKey={mod}
              stroke={getEntityColor(mod)}
              fill={getEntityColor(mod)}
              fillOpacity={0.14}
              strokeWidth={2}
            />
          ))}
          <Tooltip />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
