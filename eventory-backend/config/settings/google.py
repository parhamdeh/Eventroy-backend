"""
Google OAuth / OIDC configuration.

Google Cloud Console:
    1. Create an OAuth 2.0 Client ID of type "Web application" (or iOS/Android
       for native apps).
    2. Add authorized JavaScript origins and redirect URIs for the frontend.
    3. Put the client ID in GOOGLE_CLIENT_ID. The client secret must stay on
       the backend if the authorization-code flow is used; it must never be
       shipped in frontend code.
    4. The frontend obtains a Google ID token (GIS / authorization code +
       token exchange) and POSTs it to /api/auth/google/.
    5. This API verifies iss, aud, exp, and signature via google-auth and
       uses the stable `sub` claim as the provider identity.
"""

from config.settings.env import env

GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = env("GOOGLE_CLIENT_SECRET", default="")
