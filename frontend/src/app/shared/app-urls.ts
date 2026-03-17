export const APP_URLS = {
  backendBaseUrl: 'http://localhost:8000',
  frontendBaseUrl: 'http://localhost:4200',
} as const;

export const API_URLS = {
  accounts: `${APP_URLS.backendBaseUrl}/accounts`,
  listings: `${APP_URLS.backendBaseUrl}/listings`,
  offers: `${APP_URLS.backendBaseUrl}/offers`,
} as const;
