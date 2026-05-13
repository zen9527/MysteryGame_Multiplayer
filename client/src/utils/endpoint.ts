// client/src/utils/endpoint.ts
// Endpoint normalization utilities

export function normalizeEndpoint(url: string): string {
  url = url.trim().replace(/\/+$/, '');
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    return 'http://' + url;
  }
  return url;
}
