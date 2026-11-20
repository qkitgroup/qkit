import logging
import os

from mcp.server import MCPServer

import qkit
from qkit.agent.auth import StaticTokenVerifier

log = logging.getLogger(__name__)

SERVER_URL = "http://localhost:8000"

server = MCPServer(
    name="qkit",
    token_verifier=StaticTokenVerifier(),
    auth=StaticTokenVerifier.create_auth_settings(SERVER_URL),
    description="Qkit MCP server - Read, Execute Experiments on real hardware",
    instructions="Consult this MCP server if you need to evaluate or execute quantum experiments on real hardware"
)

@server.tool("list_devices")
def list_devices() -> list[str]:
    return qkit.instruments.get_instrument_names()


def mcp_main():
    server.run(transport="streamable-http", host="localhost", port=8000)


if __name__ == "__main__":
    qkit.start()
    if StaticTokenVerifier.MCP_TOKEN_KEY not in qkit.cfg:
        log.info(f"Setting {StaticTokenVerifier.MCP_TOKEN_KEY} from environment")
        qkit.cfg[StaticTokenVerifier.MCP_TOKEN_KEY] = os.environ[StaticTokenVerifier.MCP_TOKEN_KEY.upper()]
    mcp_main()