"""add day analytics occurred_at index

Revision ID: 81dfef998350
Revises: 21c7f18ef343
Create Date: 2026-11-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '81dfef998350'
down_revision: Union[str, Sequence[str], None] = '21c7f18ef343'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        'ix_day_analytics_occurred_at',
        'day_analytics',
        ['occurred_at'],
        unique=False,
        postgresql_using='btree',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_day_analytics_occurred_at', table_name='day_analytics')
