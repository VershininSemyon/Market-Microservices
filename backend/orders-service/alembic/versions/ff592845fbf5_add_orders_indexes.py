"""add orders indexes

Revision ID: ff592845fbf5
Revises: 25770dac5e3d
Create Date: 2026-11-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'ff592845fbf5'
down_revision: Union[str, Sequence[str], None] = '25770dac5e3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        'ix_orders_user_id',
        'orders',
        ['user_id'],
        unique=False,
        postgresql_using='btree',
    )
    op.create_index(
        'ix_outbox_events_created_at',
        'outbox_events',
        ['created_at'],
        unique=False,
        postgresql_using='btree',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_outbox_events_created_at', table_name='outbox_events')
    op.drop_index('ix_orders_user_id', table_name='orders')
