"""HR MCP tools — leave balance and calculations."""

from mcp.server.fastmcp import FastMCP

from ..erpnext_client import erpnext


def register(mcp: FastMCP):

    @mcp.tool()
    def get_leave_balance(employee: str, leave_type: str,
                          date: str = "") -> dict:
        """Get leave balance for an employee.

        Returns remaining leave days for a specific leave type.

        Args:
            employee: Employee ID (e.g. 'HR-EMP-00001')
            leave_type: Leave type (e.g. 'Annual Leave', 'Sick Leave')
            date: As-of date (YYYY-MM-DD, default: today)
        """
        return erpnext.get_leave_balance_on(employee, leave_type, date=date)

    @mcp.tool()
    def calculate_leave_days(employee: str, leave_type: str,
                             from_date: str, to_date: str) -> dict:
        """Calculate number of leave days between two dates.

        Accounts for holidays and weekends.

        Args:
            employee: Employee ID
            leave_type: Leave type (e.g. 'Annual Leave')
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
        """
        return erpnext.get_leave_days(employee, leave_type, from_date, to_date)
