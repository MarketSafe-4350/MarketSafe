declare global {
  interface Window {
    __env?: {
      apiBaseUrl?: string;
      frontendUrl?: string;
    };
  }
}

export const APP_URLS = {
  backendBaseUrl: window.__env?.apiBaseUrl ?? 'http://localhost:8000',
  frontendBaseUrl: window.__env?.frontendUrl ?? 'http://localhost:4200',
};

export const API_URLS = {
  accounts: `${APP_URLS.backendBaseUrl}/accounts`,
  listings: `${APP_URLS.backendBaseUrl}/listings`,
  offers: `${APP_URLS.backendBaseUrl}/offers`,
} as const;
