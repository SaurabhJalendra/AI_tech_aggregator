'use client';

interface ComparisonTableProps {
  data: Record<string, unknown>;
}

/**
 * ComparisonTable renders a side-by-side comparison matrix of modules
 * across multiple dimensions. Placeholder implementation.
 */
export default function ComparisonTable({ data }: ComparisonTableProps) {
  const modules = (data.modules as string[]) || [];
  const dimensions = (data.dimensions as Array<{ key: string; label: string }>) || [];

  return (
    <div className="p-6">
      <h2 className="mb-4 text-xl font-semibold">Comparison Table</h2>

      {modules.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="p-3 text-left font-medium text-gray-500">
                  Dimension
                </th>
                {modules.map((mod) => (
                  <th key={mod} className="p-3 text-left font-medium">
                    {mod}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dimensions.length > 0 ? (
                dimensions.map((dim) => (
                  <tr
                    key={dim.key}
                    className="border-b border-gray-100 dark:border-gray-800"
                  >
                    <td className="p-3 font-medium text-gray-600 dark:text-gray-400">
                      {dim.label}
                    </td>
                    {modules.map((mod) => (
                      <td key={`${mod}-${dim.key}`} className="p-3">
                        --
                      </td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    colSpan={modules.length + 1}
                    className="p-3 text-center text-gray-400"
                  >
                    No dimension data available
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="rounded-lg border-2 border-dashed border-gray-300 p-8 text-center dark:border-gray-700">
          <p className="text-gray-500">
            Comparison data will appear here when modules are compared
          </p>
        </div>
      )}
    </div>
  );
}
