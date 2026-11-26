/**
 * API client with automatic CSRF token management and JSON handling.
 */

let cachedCsrfToken: string | null = null;

export async function getCsrfToken(): Promise<string> {
  if (cachedCsrfToken) return cachedCsrfToken;
  try {
    const res = await fetch('/api/v1/csrf', { credentials: 'same-origin' });
    if (res.ok) {
      const data = await res.json();
      cachedCsrfToken = data?.data?.csrf_token || data?.csrf_token || '';
      return cachedCsrfToken || '';
    }
  } catch (err) {
    console.warn('Failed to fetch CSRF token:', err);
  }
  return '';
}

export interface ApiResponse<T = any> {
  ok: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
  message?: string;
}

export async function apiFetch<T = any>(
  url: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const headers = new Headers(options.headers || {});
  
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }

  // Attach CSRF token on mutating requests
  const method = (options.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }
    const token = await getCsrfToken();
    if (token && !headers.has('X-CSRFToken')) {
      headers.set('X-CSRFToken', token);
    }
  }

  const res = await fetch(url, {
    ...options,
    headers,
    credentials: 'same-origin',
  });

  let data: any = {};
  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    data = await res.json();
  } else {
    const text = await res.text();
    data = { ok: res.ok, message: text };
  }

  if (!res.ok) {
    const errorObj = data?.error || {
      code: `HTTP_${res.status}`,
      message: data?.message || data?.error || 'A server error occurred. Please try again.',
    };
    return {
      ok: false,
      error: errorObj,
    };
  }

  return data;
}

export async function apiGet<T = any>(url: string): Promise<ApiResponse<T>> {
  return apiFetch<T>(url, { method: 'GET' });
}

export async function apiPost<T = any>(url: string, body?: any): Promise<ApiResponse<T>> {
  return apiFetch<T>(url, {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  });
}

export async function apiDelete<T = any>(url: string, body?: any): Promise<ApiResponse<T>> {
  return apiFetch<T>(url, {
    method: 'DELETE',
    body: body ? JSON.stringify(body) : undefined,
  });
}

export async function apiPut<T = any>(url: string, body?: any): Promise<ApiResponse<T>> {
  return apiFetch<T>(url, {
    method: 'PUT',
    body: body ? JSON.stringify(body) : undefined,
  });
}
