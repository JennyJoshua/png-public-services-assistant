export type ApiHealth = {
  status: string;
  service: string;
  version: string;
};

const configuredBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();

export function getApiBaseUrl(): string | null {
  if (!configuredBaseUrl) return null;
  return configuredBaseUrl.replace(/\/+$/, "");
}

export async function checkApiHealth(signal?: AbortSignal): Promise<ApiHealth> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new Error("API base URL is not configured.");
  }

  const response = await fetch(`${baseUrl}/api/v1/health`, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw new Error(`API health check failed (HTTP ${response.status}).`);
  }

  return (await response.json()) as ApiHealth;
}
