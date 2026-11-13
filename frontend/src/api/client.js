export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request(path, { method = 'GET', token, body, signal } = {}) {
  const headers = {
    ...(body !== undefined && { 'Content-Type': 'application/json' }),
    ...(token && { Authorization: `Bearer ${token}` }),
  };

  let response;
  try {
    response = await fetch(path, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (error) {
    // Preserve intentional cancellations so App can ignore them.
    if (error.name === 'AbortError') throw error;

    throw new ApiError('Could not reach the API. Make sure the Python server is running.', 0);
  }

  // Empty or non-JSON responses become an empty object instead of failing during parsing.
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new ApiError(data.error || `Request failed (${response.status}).`, response.status);
  }

  return data;
}

export function register(credentials) {
  return request('/auth/register', { method: 'POST', body: credentials });
}

export function login(credentials) {
  return request('/auth/login', { method: 'POST', body: credentials });
}

export function loginWithGoogle(idToken) {
  return request('/auth/google', { method: 'POST', body: { id_token: idToken } });
}

export function loginWithGitHub(code) {
  return request('/auth/github', { method: 'POST', body: { code } });
}

export function getRuntime() {
  return request('/runtime');
}

export function listTasks(token, signal) {
  return request('/tasks', { token, signal });
}

export function createTask(title, submissionAt, token) {
  return request('/tasks', {
    method: 'POST',
    token,
    body: { title, ...(submissionAt && { submission_at: submissionAt }) },
  });
}

export function renameTask(id, title, submissionAt, token) {
  return request(`/tasks/${id}`, {
    method: 'PATCH',
    token,
    body: { title, submission_at: submissionAt || null },
  });
}

export function completeTask(id, token) {
  return request(`/tasks/${id}/complete`, { method: 'POST', token });
}

export function deleteTask(id, token) {
  return request(`/tasks/${id}`, { method: 'DELETE', token });
}
