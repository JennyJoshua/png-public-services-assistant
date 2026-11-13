export type ApiHealth = {
  status: string;
  service: string;
  version: string;
};

export type Citation = {
  title: string;
  institution: string;
  url: string;
  publication_date: string | null;
  last_checked_at: string;
};

export type ChatResponse = {
  request_id: string;
  answer: string;
  citations: Citation[];
  evidence: { text: string; citation_index: number }[];
  warnings: string[];
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

export async function sendChatMessage(question: string): Promise<ChatResponse> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new Error("The public services API is not configured.");
  }

  const response = await fetch(`${baseUrl}/api/v1/chat`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`The question could not be processed (HTTP ${response.status}).`);
  }

  return (await response.json()) as ChatResponse;
}
