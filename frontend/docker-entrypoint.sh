#!/bin/sh
cat > /app/src/assets/env.js << EOF
window.__env = {
  apiBaseUrl: '${API_BASE_URL:-http://localhost:8000}',
  frontendUrl: '${FRONTEND_URL:-http://localhost:4200}'
};
EOF

exec "$@"
