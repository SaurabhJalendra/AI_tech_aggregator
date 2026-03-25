'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { codeToHtml } from 'shiki';

interface ProjectFile {
  path: string;
  language: string;
  code: string;
  description?: string;
}

interface CodeProjectProps {
  data: Record<string, unknown>;
}

/** Build a simple tree structure from flat file paths */
interface TreeNode {
  name: string;
  path: string; // full path for files, prefix for folders
  isFile: boolean;
  children: TreeNode[];
}

function buildTree(files: ProjectFile[]): TreeNode[] {
  const root: TreeNode[] = [];

  for (const file of files) {
    const parts = file.path.split('/');
    let current = root;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isFile = i === parts.length - 1;
      const existing = current.find((n) => n.name === part && n.isFile === isFile);

      if (existing) {
        current = existing.children;
      } else {
        const node: TreeNode = {
          name: part,
          path: isFile ? file.path : parts.slice(0, i + 1).join('/'),
          isFile,
          children: [],
        };
        current.push(node);
        current = node.children;
      }
    }
  }

  return root;
}

function FileIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
    </svg>
  );
}

function FolderIcon({ open, className }: { open?: boolean; className?: string }) {
  return open ? (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 0 0-1.883 2.542l.857 6a2.25 2.25 0 0 0 2.227 1.932H19.05a2.25 2.25 0 0 0 2.227-1.932l.857-6a2.25 2.25 0 0 0-1.883-2.542m-16.5 0V6A2.25 2.25 0 0 1 6 3.75h3.879a1.5 1.5 0 0 1 1.06.44l2.122 2.12a1.5 1.5 0 0 0 1.06.44H18A2.25 2.25 0 0 1 20.25 9v.776" />
    </svg>
  ) : (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
    </svg>
  );
}

function TreeItem({
  node,
  depth,
  activeFile,
  onSelect,
  expandedFolders,
  onToggleFolder,
}: {
  node: TreeNode;
  depth: number;
  activeFile: string;
  onSelect: (path: string) => void;
  expandedFolders: Set<string>;
  onToggleFolder: (path: string) => void;
}) {
  const isExpanded = expandedFolders.has(node.path);
  const isActive = node.isFile && node.path === activeFile;

  return (
    <>
      <button
        className={`flex w-full items-center gap-1.5 rounded px-2 py-1 text-left text-sm transition-colors ${
          isActive
            ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300'
            : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
        }`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={() => {
          if (node.isFile) {
            onSelect(node.path);
          } else {
            onToggleFolder(node.path);
          }
        }}
      >
        {node.isFile ? (
          <FileIcon className="h-4 w-4 flex-shrink-0 text-gray-400" />
        ) : (
          <FolderIcon open={isExpanded} className="h-4 w-4 flex-shrink-0 text-yellow-500" />
        )}
        <span className="truncate">{node.name}</span>
      </button>
      {!node.isFile && isExpanded &&
        node.children.map((child) => (
          <TreeItem
            key={child.path}
            node={child}
            depth={depth + 1}
            activeFile={activeFile}
            onSelect={onSelect}
            expandedFolders={expandedFolders}
            onToggleFolder={onToggleFolder}
          />
        ))}
    </>
  );
}

export default function CodeProject({ data }: CodeProjectProps) {
  const title = (data.title as string) || 'Code Project';
  const files = (data.files as ProjectFile[]) || [];

  const [activeFile, setActiveFile] = useState<string>(files[0]?.path || '');
  const [highlightedHtml, setHighlightedHtml] = useState<string>('');
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(() => {
    // Expand all folders by default
    const folders = new Set<string>();
    for (const file of files) {
      const parts = file.path.split('/');
      for (let i = 1; i < parts.length; i++) {
        folders.add(parts.slice(0, i).join('/'));
      }
    }
    return folders;
  });

  const tree = useMemo(() => buildTree(files), [files]);
  const currentFile = useMemo(() => files.find((f) => f.path === activeFile), [files, activeFile]);

  useEffect(() => {
    if (!currentFile) {
      setHighlightedHtml('');
      return;
    }

    let cancelled = false;

    codeToHtml(currentFile.code, {
      lang: currentFile.language,
      theme: 'github-dark',
    })
      .then((html) => {
        if (!cancelled) setHighlightedHtml(html);
      })
      .catch(() => {
        if (!cancelled) setHighlightedHtml('');
      });

    return () => {
      cancelled = true;
    };
  }, [currentFile]);

  const handleToggleFolder = useCallback((path: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  }, []);

  const handleCopy = useCallback(() => {
    if (currentFile) {
      navigator.clipboard.writeText(currentFile.code).catch(() => {});
    }
  }, [currentFile]);

  if (files.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-gray-500">
        No files in this project.
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-3 dark:border-gray-700">
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="text-xs text-gray-500">
          {files.length} file{files.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Body: file tree + code view */}
      <div className="flex flex-1 overflow-hidden">
        {/* File tree sidebar */}
        <div className="w-1/4 min-w-[180px] overflow-y-auto border-r border-gray-200 bg-gray-50 py-2 dark:border-gray-700 dark:bg-gray-900/50">
          {tree.map((node) => (
            <TreeItem
              key={node.path}
              node={node}
              depth={0}
              activeFile={activeFile}
              onSelect={setActiveFile}
              expandedFolders={expandedFolders}
              onToggleFolder={handleToggleFolder}
            />
          ))}
        </div>

        {/* Code view */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {currentFile && (
            <>
              {/* File tab bar */}
              <div className="flex items-center justify-between border-b border-gray-200 bg-gray-100 px-4 py-2 dark:border-gray-700 dark:bg-gray-800">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {currentFile.path}
                  </span>
                  <span className="text-xs text-gray-400">{currentFile.language}</span>
                </div>
                <button
                  onClick={handleCopy}
                  className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  Copy
                </button>
              </div>

              {/* File description */}
              {currentFile.description && (
                <div className="border-b border-gray-200 bg-blue-50 px-4 py-1.5 text-xs text-blue-700 dark:border-gray-700 dark:bg-blue-900/20 dark:text-blue-400">
                  {currentFile.description}
                </div>
              )}

              {/* Code content */}
              <div className="flex-1 overflow-auto">
                {highlightedHtml ? (
                  <div
                    className="text-sm [&_pre]:p-4"
                    dangerouslySetInnerHTML={{ __html: highlightedHtml }}
                  />
                ) : (
                  <pre className="overflow-x-auto bg-gray-50 p-4 text-sm dark:bg-gray-900">
                    <code>{currentFile.code}</code>
                  </pre>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
