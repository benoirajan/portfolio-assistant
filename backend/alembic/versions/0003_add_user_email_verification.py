"""add_user_email_verification

Revision ID: 0003_add_user_email_verification
Revises: 0002_add_subscriptions_table
Create Date: 2026-10-12 08:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_add_user_email_verification"
down_revision: Union[str, Sequence[str], None] = "0002_add_subscriptions_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing users default to verified (server_default=sa.true()) so they aren't locked out
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "users",
        sa.Column("verification_otp", sa.String(length=6), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("otp_expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "otp_expires_at")
    op.drop_column("users", "verification_otp")
    op.drop_column("users", "is_verified")
