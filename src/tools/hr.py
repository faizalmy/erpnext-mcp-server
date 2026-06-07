"""MCP tools for HR & Payroll module.

Employee, Leave, Attendance, Expense, Payroll, Salary.
Includes Malaysia statutory validation (EPF/SOCSO/PCB).
"""

from mcp.server.fastmcp import FastMCP
from ..gateway import gateway


def register(mcp: FastMCP):

    # ── Employee ──────────────────────────────────────────

    @mcp.tool()
    def list_employees(fields: list[str] | None = None, filters: list | None = None,
                       limit: int = 20) -> dict:
        """List employees.

        Args:
            fields: Fields to return. Example: ["name", "employee_name", "department", "designation", "status"]
            filters: ERPNext filters. Example: [["Employee", "status", "=", "Active"]]
            limit: Max results
        """
        return gateway.list_documents("Employee", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_employee(name: str) -> dict:
        """Get employee details.

        Args:
            name: Employee name/ID
        """
        return gateway.get_document("Employee", name)

    @mcp.tool()
    def create_employee(employee_name: str, company: str, date_of_joining: str,
                        department: str = "", designation: str = "",
                        date_of_birth: str = "", gender: str = "",
                        cell_number: str = "", personal_email: str = "",
                        employment_type: str = "") -> dict:
        """Create a new employee record (goes through approval).

        Args:
            employee_name: Full name
            company: Company name
            date_of_joining: Join date YYYY-MM-DD
            department: Department (optional)
            designation: Job title (optional)
            date_of_birth: DOB YYYY-MM-DD (optional)
            gender: 'Male', 'Female', 'Other', 'Prefer not to say' (optional)
            cell_number: Phone number (optional)
            personal_email: Personal email (optional)
            employment_type: 'Full-time', 'Part-time', 'Contract', 'Intern' (optional)
        """
        data = {
            "employee_name": employee_name,
            "company": company,
            "date_of_joining": date_of_joining,
        }
        for k, v in {
            "department": department, "designation": designation,
            "date_of_birth": date_of_birth, "gender": gender,
            "cell_number": cell_number, "personal_email": personal_email,
            "employment_type": employment_type,
        }.items():
            if v:
                data[k] = v
        return gateway.create_employee(data)

    # ── Leave ─────────────────────────────────────────────

    @mcp.tool()
    def list_leave_applications(fields: list[str] | None = None, filters: list | None = None,
                                limit: int = 20) -> dict:
        """List leave applications.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return gateway.list_documents("Leave Application", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_leave_application(name: str) -> dict:
        """Get leave application details.

        Args:
            name: Leave Application name/ID
        """
        return gateway.get_document("Leave Application", name)

    @mcp.tool()
    def get_leave_balance(employee: str) -> dict:
        """Get all leave balances for an employee (read-only).

        Args:
            employee: Employee name/ID
        """
        return gateway.get_leave_balance(employee)

    @mcp.tool()
    def get_leave_balance_on(employee: str, leave_type: str, date: str = "") -> dict:
        """Get leave balance for a specific leave type on a date (read-only).

        Args:
            employee: Employee name/ID
            leave_type: Leave type (e.g. 'Annual Leave', 'Sick Leave')
            date: Date to check YYYY-MM-DD (optional, defaults to today)
        """
        return gateway.get_leave_balance_on(employee, leave_type, date=date)

    @mcp.tool()
    def get_leave_days(employee: str, leave_type: str, from_date: str,
                       to_date: str) -> dict:
        """Calculate number of leave days between two dates (read-only).

        Args:
            employee: Employee name/ID
            leave_type: Leave type
            from_date: Start date YYYY-MM-DD
            to_date: End date YYYY-MM-DD
        """
        return gateway.get_leave_days(employee, leave_type, from_date, to_date)

    @mcp.tool()
    def list_leave_types(fields: list[str] | None = None, limit: int = 50) -> dict:
        """List leave types (Annual, Sick, etc.).

        Args:
            fields: Fields to return
            limit: Max results
        """
        return gateway.list_documents("Leave Type", fields=fields, limit=limit)

    # ── Attendance ────────────────────────────────────────

    @mcp.tool()
    def list_attendance(fields: list[str] | None = None, filters: list | None = None,
                        limit: int = 20) -> dict:
        """List attendance records.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return gateway.list_documents("Attendance", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def list_attendance_requests(fields: list[str] | None = None, filters: list | None = None,
                                 limit: int = 20) -> dict:
        """List attendance requests (corrections).

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return gateway.list_documents("Attendance Request", fields=fields, filters=filters, limit=limit)

    # ── Expense ───────────────────────────────────────────

    @mcp.tool()
    def list_expense_claims(fields: list[str] | None = None, filters: list | None = None,
                            limit: int = 20) -> dict:
        """List expense claims.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return gateway.list_documents("Expense Claim", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_expense_claim(name: str) -> dict:
        """Get expense claim details.

        Args:
            name: Expense Claim name/ID
        """
        return gateway.get_document("Expense Claim", name)

    @mcp.tool()
    def submit_expense(employee: str, expenses: list[dict]) -> dict:
        """Submit an expense claim (goes through approval).

        Args:
            employee: Employee name/ID
            expenses: List of expense items. Each needs:
                - expense_type (str): Type of expense
                - amount (float): Amount in MYR
                - description (str): What the expense was for
                - date (str): Expense date YYYY-MM-DD
        """
        return gateway.submit_expense(employee, expenses)

    @mcp.tool()
    def make_expense_bank_entry(expense_claim: str) -> dict:
        """Create a bank entry (payment) for an approved expense claim (goes through approval).

        Args:
            expense_claim: Expense Claim name/ID
        """
        return gateway.make_expense_bank_entry(expense_claim)

    # ── Payroll ───────────────────────────────────────────

    @mcp.tool()
    def list_payroll_entries(fields: list[str] | None = None, filters: list | None = None,
                             limit: int = 20) -> dict:
        """List payroll entries (payroll runs).

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return gateway.list_documents("Payroll Entry", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_payroll_entry(name: str) -> dict:
        """Get payroll entry details.

        Args:
            name: Payroll Entry name/ID
        """
        return gateway.get_document("Payroll Entry", name)

    @mcp.tool()
    def run_payroll(company: str, month: str, year: int) -> dict:
        """Run payroll for a month (goes through approval).

        Validates Malaysia statutory rates (EPF, SOCSO, PCB, EIS).
        Preview shows per-employee breakdown.

        Args:
            company: Company name
            month: Month name (e.g. 'January', 'June')
            year: Year (e.g. 2026)
        """
        return gateway.run_payroll(company, month, year)

    @mcp.tool()
    def list_salary_slips(fields: list[str] | None = None, filters: list | None = None,
                          limit: int = 20) -> dict:
        """List salary slips.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return gateway.list_documents("Salary Slip", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_salary_slip(name: str) -> dict:
        """Get salary slip details with earnings and deductions.

        Args:
            name: Salary Slip name/ID
        """
        return gateway.get_document("Salary Slip", name)

    @mcp.tool()
    def list_salary_structures(fields: list[str] | None = None, limit: int = 20) -> dict:
        """List salary structures (pay component templates).

        Args:
            fields: Fields to return
            limit: Max results
        """
        return gateway.list_documents("Salary Structure", fields=fields, limit=limit)

    # ── Loan ──────────────────────────────────────────────

    @mcp.tool()
    def list_loans(fields: list[str] | None = None, filters: list | None = None,
                   limit: int = 20) -> dict:
        """List employee loans.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return gateway.list_documents("Loan", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_loan(name: str) -> dict:
        """Get loan details.

        Args:
            name: Loan name/ID
        """
        return gateway.get_document("Loan", name)

    # ── Departments & Designations ────────────────────────

    @mcp.tool()
    def list_departments(fields: list[str] | None = None, limit: int = 50) -> dict:
        """List departments.

        Args:
            fields: Fields to return
            limit: Max results
        """
        return gateway.list_documents("Department", fields=fields, limit=limit)

    @mcp.tool()
    def list_designations(fields: list[str] | None = None, limit: int = 50) -> dict:
        """List job designations/titles.

        Args:
            fields: Fields to return
            limit: Max results
        """
        return gateway.list_documents("Designation", fields=fields, limit=limit)
