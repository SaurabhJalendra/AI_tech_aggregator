'use client';

import CodeBlock, { type CodeBlockData } from './CodeBlock';

interface CodePreviewProps {
  data: Record<string, unknown>;
}

export default function CodePreview({ data }: CodePreviewProps) {
  return <CodeBlock data={data as CodeBlockData} />;
}
