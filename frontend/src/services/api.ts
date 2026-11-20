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
      const body = await response.text();
      let detail = body;
      try {
        const parsed: unknown = JSON.parse(body);
        if (parsed && typeof parsed === "object" && "detail" in parsed) {
          const apiDetail = parsed.detail;
          if (typeof apiDetail === "string") {
            detail = apiDetail;
          } else if (
            apiDetail &&
            typeof apiDetail === "object" &&
            "message" in apiDetail &&
            typeof apiDetail.message === "string"
          ) {
            detail = apiDetail.message;
          } else if (Array.isArray(apiDetail)) {
            detail = apiDetail
              .map((item) =>
                item && typeof item === "object" && "msg" in item
                  ? String(item.msg)
                  : "",
              )
              .filter(Boolean)
              .join("; ");
          }
        }
      } catch {
        // Keep the response body as-is when the server does not return JSON.
      }
      throw new Error(
        detail || `API request failed: ${response.status} ${response.statusText}`,
      );
    }

    if (response.status === 204) return undefined as T;

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
