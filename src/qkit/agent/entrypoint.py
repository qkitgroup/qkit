from mcp.server import MCPServer

import qkit

server = MCPServer("qkit")

@server.tool("list_devices")
def list_devices() -> list[str]:
    return qkit.instruments.get_instrument_names()


def mcp_main():
    server.run(transport="streamable-http")


if __name__ == "__main__":
    qkit.start()
    mcp_main()