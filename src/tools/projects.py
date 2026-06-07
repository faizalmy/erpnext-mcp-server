"""MCP tools for Projects module.

Project, Task, Timesheet, Activity Type.
"""

from mcp.server.fastmcp import FastMCP
from ..erpnext_client import erpnext


def register(mcp: FastMCP):

    @mcp.tool()
    def list_projects(fields: list[str] | None = None, filters: list | None = None,
                      limit: int = 20) -> dict:
        """List projects.

        Args:
            fields: Fields to return. Example: ["name", "project_name", "status", "percent_complete"]
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Project", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_project(name: str) -> dict:
        """Get project details.

        Args:
            name: Project name/ID
        """
        return erpnext.get_document("Project", name)

    @mcp.tool()
    def create_project(project_name: str, company: str = "",
                       expected_start_date: str = "", expected_end_date: str = "") -> dict:
        """Create a new project.

        Args:
            project_name: Project name
            company: Company name (optional)
            expected_start_date: Start date YYYY-MM-DD (optional)
            expected_end_date: End date YYYY-MM-DD (optional)
        """
        data = {"project_name": project_name}
        if company:
            data["company"] = company
        if expected_start_date:
            data["expected_start_date"] = expected_start_date
        if expected_end_date:
            data["expected_end_date"] = expected_end_date
        return erpnext.create_document("Project", data)

    @mcp.tool()
    def list_tasks(fields: list[str] | None = None, filters: list | None = None,
                   limit: int = 20) -> dict:
        """List tasks.

        Args:
            fields: Fields to return. Example: ["name", "subject", "project", "status", "priority"]
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Task", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_task(name: str) -> dict:
        """Get task details.

        Args:
            name: Task name/ID
        """
        return erpnext.get_document("Task", name)

    @mcp.tool()
    def create_task(subject: str, project: str = "", priority: str = "Medium",
                    status: str = "Open", exp_start_date: str = "",
                    exp_end_date: str = "") -> dict:
        """Create a new task.

        Args:
            subject: Task title/subject
            project: Project name/ID (optional)
            priority: 'Low', 'Medium', 'High', 'Urgent'
            status: 'Open', 'Working', 'Pending', 'Completed', 'Cancelled'
            exp_start_date: Expected start date YYYY-MM-DD (optional)
            exp_end_date: Expected end date YYYY-MM-DD (optional)
        """
        data = {"subject": subject, "priority": priority, "status": status}
        if project:
            data["project"] = project
        if exp_start_date:
            data["exp_start_date"] = exp_start_date
        if exp_end_date:
            data["exp_end_date"] = exp_end_date
        return erpnext.create_document("Task", data)

    @mcp.tool()
    def list_timesheets(fields: list[str] | None = None, filters: list | None = None,
                        limit: int = 20) -> dict:
        """List timesheets.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Timesheet", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_timesheet(name: str) -> dict:
        """Get timesheet details.

        Args:
            name: Timesheet name/ID
        """
        return erpnext.get_document("Timesheet", name)

    @mcp.tool()
    def make_sales_invoice_from_timesheet(timesheet: str) -> dict:
        """Create a sales invoice from a timesheet.

        Args:
            timesheet: Timesheet name/ID
        """
        return erpnext.make_sales_invoice_from_timesheet(timesheet)
