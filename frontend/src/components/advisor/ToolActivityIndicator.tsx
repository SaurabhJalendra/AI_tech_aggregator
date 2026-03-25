'use client';

import type { ToolActivity } from '@/types/chat';

interface ToolActivityIndicatorProps {
  activities: ToolActivity[];
  hasContent: boolean;
}

export default function ToolActivityIndicator({ activities, hasContent }: ToolActivityIndicatorProps) {
  // When text content has arrived, only show running activities
  const visible = hasContent
    ? activities.filter((a) => a.status === 'running')
    : activities;

  if (visible.length === 0) return null;

  return (
    <div className="mb-2 space-y-1">
      {visible.map((activity, i) => (
        <div
          key={`${activity.tool}-${i}`}
          className="flex items-center gap-2 text-xs"
        >
          {activity.status === 'running' ? (
            <>
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-500" />
              </span>
              <span className="text-gray-500 dark:text-gray-400">
                {activity.message || `Using ${activity.tool}...`}
              </span>
            </>
          ) : (
            <>
              <span className="text-green-500">&#10003;</span>
              <span className="text-gray-400 dark:text-gray-500">
                {activity.message || `${activity.tool} complete`}
              </span>
            </>
          )}
        </div>
      ))}
    </div>
  );
}
