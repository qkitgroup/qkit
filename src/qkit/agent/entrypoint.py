import logging
import os

from mcp.server import MCPServer

import qkit
from qkit.agent import tls
from qkit.agent.auth import StaticTokenVerifier
import anyio
import uvicorn

log = logging.getLogger(__name__)

tls_settings = tls.TLSConfig()
server = MCPServer(
    name="qkit",
    token_verifier=StaticTokenVerifier(),
    auth=StaticTokenVerifier.create_auth_settings(tls_settings.get_base_url()),
    description="Qkit MCP server - Read, Execute Experiments on real hardware",
    instructions="Consult this MCP server if you need to evaluate or execute quantum experiments on real hardware"
)

@server.tool("list_devices")
def list_devices() -> list[str]:
    return qkit.instruments.get_instrument_names()


def mcp_main():

    host, port = tls_settings.get_bind_address()

    app = server.streamable_http_app(host=host)
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level=server.settings.log_level.lower(),
        **tls_settings.get_ssl_kwargs(),
    )
    log.info("Serving the MCP server over HTTPS on %s:%s", host, port)
    anyio.run(uvicorn.Server(config).serve)


if __name__ == "__main__":
    qkit.start()
    if StaticTokenVerifier.MCP_TOKEN_KEY not in qkit.cfg:
        log.info(f"Setting {StaticTokenVerifier.MCP_TOKEN_KEY} from environment")
        qkit.cfg[StaticTokenVerifier.MCP_TOKEN_KEY] = os.environ[StaticTokenVerifier.MCP_TOKEN_KEY.upper()]
    mcp_main()