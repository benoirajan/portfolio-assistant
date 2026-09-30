"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-25 21:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('tier', sa.String(length=20), nullable=False, server_default='FREE'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False, server_default='Default Portfolio'),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('total_investment', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('current_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_pnl', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_pnl_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('raw_summary', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_portfolios_token_hash'), 'portfolios', ['token_hash'], unique=True)
    op.create_index(op.f('ix_portfolios_user_id'), 'portfolios', ['user_id'], unique=False)

    # User Holdings table
    op.create_table(
        'user_holdings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('portfolio_id', sa.String(length=36), nullable=False),
        sa.Column('tradingsymbol', sa.String(length=100), nullable=False),
        sa.Column('exchange', sa.String(length=20), nullable=False, server_default='NSE'),
        sa.Column('isin', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_price', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('last_price', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('close_price', sa.Float(), nullable=True),
        sa.Column('pnl', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('pnl_percentage', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('sector', sa.String(length=100), nullable=True),
        sa.Column('cap_category', sa.String(length=50), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_holdings_portfolio_id'), 'user_holdings', ['portfolio_id'], unique=False)
    op.create_index(op.f('ix_user_holdings_tradingsymbol'), 'user_holdings', ['tradingsymbol'], unique=False)

    # User Sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('enctoken_encrypted', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_sessions_token_hash'), 'user_sessions', ['token_hash'], unique=False)
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('user_sessions')
    op.drop_table('user_holdings')
    op.drop_table('portfolios')
    op.drop_table('users')
