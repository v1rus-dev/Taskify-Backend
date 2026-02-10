"""add spaces core mvp

Revision ID: 20260209_01
Revises:
Create Date: 2026-02-09 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260209_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "spaces",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_lightweight", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_spaces_id"), "spaces", ["id"], unique=False)
    op.create_index(op.f("ix_spaces_created_by"), "spaces", ["created_by"], unique=False)
    op.create_index(op.f("ix_spaces_client_id"), "spaces", ["client_id"], unique=False)

    op.create_table(
        "space_members",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("space_id", sa.BigInteger(), sa.ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("space_id", "user_id", name="uq_space_members_space_user"),
    )
    op.create_index(op.f("ix_space_members_id"), "space_members", ["id"], unique=False)
    op.create_index(op.f("ix_space_members_space_id"), "space_members", ["space_id"], unique=False)
    op.create_index(op.f("ix_space_members_user_id"), "space_members", ["user_id"], unique=False)

    op.create_table(
        "space_invites",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("space_id", sa.BigInteger(), sa.ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("inviter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("token", name="uq_space_invites_token"),
    )
    op.create_index(op.f("ix_space_invites_id"), "space_invites", ["id"], unique=False)
    op.create_index(op.f("ix_space_invites_space_id"), "space_invites", ["space_id"], unique=False)
    op.create_index(op.f("ix_space_invites_inviter_id"), "space_invites", ["inviter_id"], unique=False)
    op.create_index(op.f("ix_space_invites_token"), "space_invites", ["token"], unique=False)
    op.create_index(op.f("ix_space_invites_expires_at"), "space_invites", ["expires_at"], unique=False)

    op.create_table(
        "space_task_lists",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("space_id", sa.BigInteger(), sa.ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("order", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("space_id", "client_id", name="uq_space_task_lists_space_client_id"),
    )
    op.create_index(op.f("ix_space_task_lists_id"), "space_task_lists", ["id"], unique=False)
    op.create_index(op.f("ix_space_task_lists_space_id"), "space_task_lists", ["space_id"], unique=False)
    op.create_index(op.f("ix_space_task_lists_client_id"), "space_task_lists", ["client_id"], unique=False)

    op.create_table(
        "space_tasks",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("space_id", sa.BigInteger(), sa.ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("list_id", sa.BigInteger(), sa.ForeignKey("space_task_lists.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assignee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("claimed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("space_id", "client_id", name="uq_space_tasks_space_client_id"),
    )
    op.create_index(op.f("ix_space_tasks_id"), "space_tasks", ["id"], unique=False)
    op.create_index(op.f("ix_space_tasks_space_id"), "space_tasks", ["space_id"], unique=False)
    op.create_index(op.f("ix_space_tasks_list_id"), "space_tasks", ["list_id"], unique=False)
    op.create_index(op.f("ix_space_tasks_assignee_id"), "space_tasks", ["assignee_id"], unique=False)
    op.create_index(op.f("ix_space_tasks_claimed_by_id"), "space_tasks", ["claimed_by_id"], unique=False)
    op.create_index(op.f("ix_space_tasks_client_id"), "space_tasks", ["client_id"], unique=False)
    op.create_index(op.f("ix_space_tasks_completed_at"), "space_tasks", ["completed_at"], unique=False)

    op.create_table(
        "space_subtasks",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("space_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("task_id", "client_id", name="uq_space_subtasks_task_client_id"),
    )
    op.create_index(op.f("ix_space_subtasks_id"), "space_subtasks", ["id"], unique=False)
    op.create_index(op.f("ix_space_subtasks_task_id"), "space_subtasks", ["task_id"], unique=False)
    op.create_index(op.f("ix_space_subtasks_client_id"), "space_subtasks", ["client_id"], unique=False)

    op.create_table(
        "space_notes",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("space_id", sa.BigInteger(), sa.ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("space_id", "client_id", name="uq_space_notes_space_client_id"),
    )
    op.create_index(op.f("ix_space_notes_id"), "space_notes", ["id"], unique=False)
    op.create_index(op.f("ix_space_notes_space_id"), "space_notes", ["space_id"], unique=False)
    op.create_index(op.f("ix_space_notes_client_id"), "space_notes", ["client_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_space_notes_client_id"), table_name="space_notes")
    op.drop_index(op.f("ix_space_notes_space_id"), table_name="space_notes")
    op.drop_index(op.f("ix_space_notes_id"), table_name="space_notes")
    op.drop_table("space_notes")

    op.drop_index(op.f("ix_space_subtasks_client_id"), table_name="space_subtasks")
    op.drop_index(op.f("ix_space_subtasks_task_id"), table_name="space_subtasks")
    op.drop_index(op.f("ix_space_subtasks_id"), table_name="space_subtasks")
    op.drop_table("space_subtasks")

    op.drop_index(op.f("ix_space_tasks_completed_at"), table_name="space_tasks")
    op.drop_index(op.f("ix_space_tasks_client_id"), table_name="space_tasks")
    op.drop_index(op.f("ix_space_tasks_claimed_by_id"), table_name="space_tasks")
    op.drop_index(op.f("ix_space_tasks_assignee_id"), table_name="space_tasks")
    op.drop_index(op.f("ix_space_tasks_list_id"), table_name="space_tasks")
    op.drop_index(op.f("ix_space_tasks_space_id"), table_name="space_tasks")
    op.drop_index(op.f("ix_space_tasks_id"), table_name="space_tasks")
    op.drop_table("space_tasks")

    op.drop_index(op.f("ix_space_task_lists_client_id"), table_name="space_task_lists")
    op.drop_index(op.f("ix_space_task_lists_space_id"), table_name="space_task_lists")
    op.drop_index(op.f("ix_space_task_lists_id"), table_name="space_task_lists")
    op.drop_table("space_task_lists")

    op.drop_index(op.f("ix_space_invites_expires_at"), table_name="space_invites")
    op.drop_index(op.f("ix_space_invites_token"), table_name="space_invites")
    op.drop_index(op.f("ix_space_invites_inviter_id"), table_name="space_invites")
    op.drop_index(op.f("ix_space_invites_space_id"), table_name="space_invites")
    op.drop_index(op.f("ix_space_invites_id"), table_name="space_invites")
    op.drop_table("space_invites")

    op.drop_index(op.f("ix_space_members_user_id"), table_name="space_members")
    op.drop_index(op.f("ix_space_members_space_id"), table_name="space_members")
    op.drop_index(op.f("ix_space_members_id"), table_name="space_members")
    op.drop_table("space_members")

    op.drop_index(op.f("ix_spaces_client_id"), table_name="spaces")
    op.drop_index(op.f("ix_spaces_created_by"), table_name="spaces")
    op.drop_index(op.f("ix_spaces_id"), table_name="spaces")
    op.drop_table("spaces")
