const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

export async function getModules(params?: {
  category?: string;
  search?: string;
  page?: number;
  page_size?: number;
}) {
  const searchParams = new URLSearchParams();
  if (params?.category) searchParams.set('category', params.category);
  if (params?.search) searchParams.set('search', params.search);
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.page_size) searchParams.set('page_size', String(params.page_size));

  const qs = searchParams.toString();
  return fetchAPI<{ modules: import('@/types/module').ModuleSummary[]; total: number }>(
    `/modules${qs ? `?${qs}` : ''}`
  );
}

export async function getModule(slug: string) {
  return fetchAPI<import('@/types/module').ModuleDetail>(`/modules/${slug}`);
}

export async function getCategories() {
  return fetchAPI<import('@/types/module').CategoryResponse[]>('/modules/categories');
}

export async function compareModules(slugs: string[], weights?: Record<string, number>) {
  return fetchAPI<import('@/types/module').ComparisonResult>('/compare', {
    method: 'POST',
    body: JSON.stringify({ slugs, weights }),
  });
}
