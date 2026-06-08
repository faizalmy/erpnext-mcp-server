"""Test erpnext-mcp-server via stdio transport using the official MCP client SDK."""
import asyncio
import json
import pathlib
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Project root (one level up from tests/)
ROOT = pathlib.Path(__file__).resolve().parent.parent


async def main():
    server = StdioServerParameters(
        command=str(ROOT / '.venv' / 'bin' / 'python'),
        args=['-m', 'src.server'],
        cwd=str(ROOT),
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. Initialize
            info = await session.initialize()
            print(f'=== 1. Initialize ===')
            print(f'Server: {info.serverInfo.name} v{info.serverInfo.version}')
            caps = info.capabilities
            print(f'Tools: {hasattr(caps, "tools")}  Resources: {hasattr(caps, "resources")}  Prompts: {hasattr(caps, "prompts")}')

            # 2. List tools
            tools_resp = await session.list_tools()
            tools = tools_resp.tools
            print(f'\n=== 2. Tools: {len(tools)} total ===')

            # Show annotation on delete_Customer
            del_cust = next((t for t in tools if t.name == 'delete_Customer'), None)
            if del_cust:
                print(f'delete_Customer: destructive={del_cust.annotations.destructiveHint} readOnly={del_cust.annotations.readOnlyHint}')

            # Count categories
            auto = [t for t in tools if t.name.startswith(('list_', 'get_', 'create_', 'update_', 'delete_'))]
            curated = [t for t in tools if t not in auto]
            print(f'Auto-discovered CRUD: {len(auto)}  Curated: {len(curated)}')

            # 3. Call list_Customer
            print(f'\n=== 3. list_Customer ===')
            result = await session.call_tool('list_Customer', {'limit': 3})
            if result.isError:
                print(f'  ERROR: {result.content[0].text}')
            else:
                data = json.loads(result.content[0].text)
                print(f'  Count: {data["count"]}')
                for c in data.get('data', []):
                    print(f'    {c.get("name", c)}')

            # 4. Call get_Customer
            print(f'\n=== 4. get_Customer ===')
            result = await session.call_tool('get_Customer', {'name': 'Acme Sdn Bhd'})
            if result.isError:
                print(f'  ERROR: {result.content[0].text}')
            else:
                data = json.loads(result.content[0].text)
                print(f'  customer_name: {data.get("customer_name", "N/A")}')
                print(f'  group: {data.get("customer_group", "N/A")}')
                print(f'  territory: {data.get("territory", "N/A")}')

            # 5. Call list_Sales_Invoice
            print(f'\n=== 5. list_Sales_Invoice ===')
            result = await session.call_tool('list_Sales_Invoice', {'limit': 3})
            if result.isError:
                print(f'  ERROR: {result.content[0].text}')
            else:
                data = json.loads(result.content[0].text)
                print(f'  Count: {data["count"]}')
                for inv in data.get('data', []):
                    print(f'    {inv.get("name", "?")} | {inv.get("customer", "?")} | {inv.get("grand_total", "?")}')

            # 6. Call list_Item
            print(f'\n=== 6. list_Item ===')
            result = await session.call_tool('list_Item', {'limit': 3})
            if result.isError:
                print(f'  ERROR: {result.content[0].text}')
            else:
                data = json.loads(result.content[0].text)
                print(f'  Count: {data["count"]}')
                for item in data.get('data', []):
                    print(f'    {item.get("name", "?")} | {item.get("item_group", "?")}')

            # 7. Curated: get_account_balance
            print(f'\n=== 7. get_account_balance (curated) ===')
            result = await session.call_tool('get_account_balance', {'account': 'Debtors - ACT'})
            if result.isError:
                print(f'  ERROR: {result.content[0].text[:150]}')
            else:
                print(f'  {result.content[0].text[:200]}')

            # 8. Curated: get_fiscal_year
            print(f'\n=== 8. get_fiscal_year (curated) ===')
            result = await session.call_tool('get_fiscal_year', {'date': '2026-06-08'})
            if result.isError:
                print(f'  ERROR: {result.content[0].text[:150]}')
            else:
                print(f'  {result.content[0].text[:200]}')

            # 9. Resources
            print(f'\n=== 9. Resources ===')
            resources_resp = await session.list_resources()
            resources = resources_resp.resources
            print(f'  Total: {len(resources)}')
            for r in resources:
                print(f'    {r.uri}')

            # 10. Read erpnext://companies
            print(f'\n=== 10. Read erpnext://companies ===')
            result = await session.read_resource('erpnext://companies')
            text = result.contents[0].text
            data = json.loads(text)
            print(f'  Companies: {len(data["data"])}')
            for co in data['data']:
                print(f'    {co["name"]}')

            # 11. Prompts
            print(f'\n=== 11. Prompts ===')
            prompts_resp = await session.list_prompts()
            prompts = prompts_resp.prompts
            print(f'  Total: {len(prompts)}')
            for p in prompts:
                print(f'    {p.name}: {p.description[:60]}')

            print(f'\n=== ALL STDIO TESTS PASSED ===')


asyncio.run(main())
