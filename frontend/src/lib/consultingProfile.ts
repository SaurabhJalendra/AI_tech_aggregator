const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function fetchConsultingProfile(): Promise<Record<string, unknown> | null> {
  try {
    const res = await fetch(`${apiBase}/advisor/consulting/profile`, {
      headers: { Authorization: 'Bearer dev@example.com' },
    });
    if (!res.ok) return null;
    const data = await res.json();
    return (data.consulting_profile as Record<string, unknown>) ?? null;
  } catch {
    return null;
  }
}
