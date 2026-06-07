"""MCP tools for HR operations.

Employees, payroll, leave, and expenses.
Payroll includes Malaysia statutory validation (EPF/SOCSO/PCB).
"""

from mcp.server.fastmcp import FastMCP

from ..gateway import gateway


def register(mcp: FastMCP):
    """Register HR tools on the MCP server."""

    @mcp.tool()
    def create_employee(data: dict) -> dict:
        """Create a new employee record (goes through approval).

        Args:
            data: Employee fields. Required:
                - employee_name (str): Full name
                - company (str): Company name
                - date_of_joining (str): Join date (YYYY-MM-DD)
            Optional: department, designation, date_of_birth, gender,
                cell_number, personal_email, etc.

        Returns:
            Intent with preview for approval.
        """
        return gateway.create_employee(data=data)

    @mcp.tool()
    def run_payroll(
        company: str,
        month: str,
        year: int,
    ) -> dict:
        """Run payroll for a month (goes through approval).

        Validates Malaysia statutory rates (EPF, SOCSO, PCB, EIS)
        before execution. Preview shows per-employee breakdown.

        Args:
            company: Company name
            month: Month name (e.g. 'January', 'June')
            year: Year (e.g. 2026)

        Returns:
            Intent with preview showing gross, deductions (EPF/SOCSO/PCB),
            net pay, and total employer cost.
        """
        return gateway.run_payroll(
            company=company, month=month, year=year
        )

    @mcp.tool()
    def get_leave_balance(employee: str) -> dict:
        """Get leave balance for an employee (read-only).

        Args:
            employee: Employee name or ID

        Returns:
            Leave balances by type (annual, sick, etc.) with ai_context.
        """
        return gateway.get_leave_balance(employee=employee)

    @mcp.tool()
    def submit_expense(employee: str, expenses: list[dict]) -> dict:
        """Submit an expense claim (goes through approval).

        Args:
            employee: Employee name or ID
            expenses: List of expense items. Each needs:
                - expense_type (str): Type of expense
                - amount (float): Amount in MYR
                - description (str): What the expense was for
                - date (str): Expense date (YYYY-MM-DD)

        Returns:
            Intent with preview showing total and per-item breakdown.
        """
        return gateway.submit_expense(
            employee=employee, expenses=expenses
        )
