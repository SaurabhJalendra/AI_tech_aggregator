'use client';

interface ArchitectureDiagramProps {
  data: Record<string, unknown>;
}

/**
 * ArchitectureDiagram renders an interactive architecture diagram using
 * React Flow. This is a placeholder that will be fully implemented later.
 */
export default function ArchitectureDiagram({ data }: ArchitectureDiagramProps) {
  const title = (data.title as string) || 'Architecture Diagram';
  const description = (data.description as string) || '';
  const nodes = data.nodes as unknown[] | undefined;

  return (
    <div className="flex h-full flex-col p-6">
      <h2 className="mb-2 text-xl font-semibold">{title}</h2>
      {description && (
        <p className="mb-4 text-sm text-gray-600 dark:text-gray-400">
          {description}
        </p>
      )}
      <div className="flex flex-1 items-center justify-center rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700">
        <div className="text-center">
          <p className="text-gray-500">
            Architecture diagram will render here
          </p>
          <p className="mt-2 text-sm text-gray-400">
            Powered by React Flow
          </p>
          {nodes && (
            <p className="mt-2 text-xs text-gray-400">
              {nodes.length} nodes configured
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
