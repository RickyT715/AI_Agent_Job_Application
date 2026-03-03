"""Add generated_resumes table.

Revision ID: 002
Revises: 001
Create Date: 2026-03-02
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "generated_resumes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "match_id", sa.Integer(), sa.ForeignKey("match_results.id"), nullable=False
        ),
        sa.Column("external_task_id", sa.String(255), nullable=False),
        sa.Column(
            "status", sa.String(50), nullable=False, server_default="pending"
        ),
        sa.Column("resume_pdf_path", sa.String(500), nullable=True),
        sa.Column("cover_letter_pdf_path", sa.String(500), nullable=True),
        sa.Column("cover_letter_text", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("provider", sa.String(50), nullable=False, server_default="anthropic"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_generated_resume_match_id", "generated_resumes", ["match_id"]
    )
    op.create_index(
        "ix_generated_resume_external_task_id",
        "generated_resumes",
        ["external_task_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_generated_resume_external_task_id", table_name="generated_resumes")
    op.drop_index("ix_generated_resume_match_id", table_name="generated_resumes")
    op.drop_table("generated_resumes")
