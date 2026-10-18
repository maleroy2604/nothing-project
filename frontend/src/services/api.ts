export async function apiRequest<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`/api${path}`, init);

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      detail || `API request failed: ${response.status} ${response.statusText}`,
    );
  }

  return (await response.json()) as T;
}
