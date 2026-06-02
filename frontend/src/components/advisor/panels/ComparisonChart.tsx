'use client';

import ComparisonDecisionSurface from './ComparisonDecisionSurface';

interface ComparisonChartProps {
  data: Record<string, unknown>;
}

/**
 * Comparison panel entry — renders the decision surface by default.
 * Panel type remains `comparison_chart` for API compatibility.
 */
export default function ComparisonChart({ data }: ComparisonChartProps) {
  return <ComparisonDecisionSurface data={data} />;
}
