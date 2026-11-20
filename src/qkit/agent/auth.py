import logging
import secrets

from mcp.server.auth.provider import TokenVerifier, AccessToken
from mcp.server.auth.settings import AuthSettings

import qkit

log = logging.getLogger(__name__)

class StaticTokenVerifier(TokenVerifier):

    MCP_TOKEN_KEY = "mcp_token"

    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(32)

    @property
    def token(self) -> str:
        if self.MCP_TOKEN_KEY not in qkit.cfg:
            log.warning("No MCP token found in configuration. Generating a temporary key.")
            qkit.cfg[self.MCP_TOKEN_KEY] = self.generate_token()
            log.warning("Temporary key: %s", qkit.cfg[self.MCP_TOKEN_KEY])
        return qkit.cfg[self.MCP_TOKEN_KEY]

    async def verify_token(self, token: str) -> AccessToken | None:
        if secrets.compare_digest(self.token, token):
            return AccessToken(token=token, client_id="static-token", scopes=[])
        return None

    @staticmethod
    def create_auth_settings(base_url: str) -> AuthSettings:
        return AuthSettings.model_validate({
            "issuer_url": base_url,
            "resource_server_url": f"{base_url}/mcp",
            "validate_token_resource": False
        })