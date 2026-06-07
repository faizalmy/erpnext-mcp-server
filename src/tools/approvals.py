"""MCP tools for approval workflow management.

Agents use these tools to check on pending intents,
approve/reject them, and view the audit trail.
"""

from mcp.server.fastmcp import FastMCP

from ..gateway import gateway


def register(mcp: FastMCP):
    """Register approval tools on the MCP server."""

    @mcp.tool()
    def list_intents(status: str = "") -> dict:
        """List intents (approval requests), optionally filtered by status.

        Status values: 'pending', 'approved', 'rejected', 'executed', 'failed'

        Args:
            status: Filter by status (empty = all)

        Returns:
            List of intents with details.
        """
        return gateway.list_intents(status=status)

    @mcp.tool()
    def approve_intent(
        intent_id: str,
        reviewed_by: str = "human:faizal",
    ) -> dict:
        """Approve a pending intent to execute via ERPNext.

        Once approved, the gateway executes the action through ERPNext's
        deterministic engine — all financial numbers are calculated by
        ERPNext, never by the AI agent.

        Args:
            intent_id: The intent ID (from create_invoice, etc.)
            reviewed_by: Who is approving (default: human:faizal)

        Returns:
            Execution result with invoice/payment details and ai_context.
        """
        return gateway.approve_intent(
            intent_id=intent_id, reviewed_by=reviewed_by
        )

    @mcp.tool()
    def reject_intent(
        intent_id: str,
        reason: str = "",
        reviewed_by: str = "human:faizal",
    ) -> dict:
        """Reject a pending intent. The action will NOT be executed.

        Args:
            intent_id: The intent ID to reject
            reason: Why the intent is being rejected
            reviewed_by: Who is rejecting (default: human:faizal)

        Returns:
            Confirmation of rejection.
        """
        return gateway.reject_intent(
            intent_id=intent_id, reason=reason, reviewed_by=reviewed_by
        )

    @mcp.tool()
    def get_audit_log(limit: int = 50) -> dict:
        """Get the audit trail of all actions.

        Shows who did what, when, and the result. Every action is logged:
        agent proposals, human approvals/rejections, and ERPNext executions.

        Args:
            limit: Max entries to return (default 50)

        Returns:
            Audit log entries with timestamps, performers, and outcomes.
        """
        return gateway.get_audit_log(limit=limit)
