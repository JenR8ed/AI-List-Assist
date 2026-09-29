// Browser requests use the signed local Flask session, never the server API key.
function apiFetch(path, options = {}) {
    const method = (options.method || 'GET').toUpperCase();
    const headers = new Headers(options.headers || {});
    if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
        headers.set('X-CSRF-Token', document.querySelector('meta[name="csrf-token"]').content);
    }
    return window.fetch(path, { ...options, headers, credentials: 'same-origin' });
}
