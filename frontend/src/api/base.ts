// Empty by default: the frontend and the API share the same origin
// (nginx proxies /map, /data, /country, ... to FastAPI). During `vite`
// development the same paths are proxied by Vite, see vite.config.ts.
// Set VITE_API_URL only when the API lives on another origin.
const configuredApiUrl = import.meta.env.VITE_API_URL?.trim().replace(/\/+$/, '')

export const API_URL = configuredApiUrl ?? ''
