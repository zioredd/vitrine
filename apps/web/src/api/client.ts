export interface ApiEnvelope<T> {
  data: T;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

export async function apiClient<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, headers, ...rest } = options;

  const response = await fetch(path, {
    method: "GET",
    ...rest,
    headers: {
      Accept: "application/json",
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new ApiError(text || `Request failed (${response.status})`, response.status);
  }

  const payload = (await response.json()) as ApiEnvelope<T>;
  return payload.data;
}

export function apiGet<T>(path: string) {
  return apiClient<T>(path, { method: "GET" });
}

export function apiPost<T>(path: string, body?: unknown) {
  return apiClient<T>(path, { method: "POST", body });
}
