"""add_user_ai_quota_tracking

Revision ID: 0004_add_user_ai_quota_tracking
Revises: 0003_add_user_email_verification
Create Date: 2026-11-14 17:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004_add_user_ai_quota_tracking"
down_revision: Union[str, Sequence[str], None] = "0003_add_user_email_verification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("ai_quota_used", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("ai_quota_reset_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "ai_quota_reset_at")
    op.drop_column("users", "ai_quota_used")

