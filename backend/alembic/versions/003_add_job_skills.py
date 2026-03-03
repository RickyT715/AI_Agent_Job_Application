"""Add job_skills table.

Revision ID: 003
Revises: 002
Create Date: 2026-03-02
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "job_id",
            sa.Integer(),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("skill_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
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
    op.create_unique_constraint("uq_job_skill", "job_skills", ["job_id", "skill_name"])
    op.create_index("ix_job_skill_skill_name", "job_skills", ["skill_name"])
    op.create_index("ix_job_skill_job_id", "job_skills", ["job_id"])
    op.create_index("ix_job_skill_category", "job_skills", ["category"])


def downgrade() -> None:
    op.drop_index("ix_job_skill_category", table_name="job_skills")
    op.drop_index("ix_job_skill_job_id", table_name="job_skills")
    op.drop_index("ix_job_skill_skill_name", table_name="job_skills")
    op.drop_constraint("uq_job_skill", "job_skills", type_="unique")
    op.drop_table("job_skills")
