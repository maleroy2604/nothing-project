export async function apiRequest<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const method = init?.method ?? "GET";
  const startTime = performance.now();
  let statusCode: number | undefined;

  try {
    const response = await fetch(`/api${path}`, init);
    statusCode = response.status;

    if (!response.ok) {
      const detail = await response.text();
      throw new Error(
        detail || `API request failed: ${response.status} ${response.statusText}`,
      );
    }

    const data = (await response.json()) as T;
    if (import.meta.env.DEV) {
      console.info(
        `[api] ${method} ${path} ${response.status} (${(performance.now() - startTime).toFixed(0)} ms)`,
      );
    }

    return data;
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error(
        `[api] ${method} ${path} failed${statusCode !== undefined ? ` with ${statusCode}` : ""} (${(performance.now() - startTime).toFixed(0)} ms; ${error instanceof Error ? error.name : "unknown error"})`,
      );
    }
    throw error;
  }
}
