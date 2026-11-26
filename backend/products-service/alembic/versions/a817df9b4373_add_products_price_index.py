"""add products price index

Revision ID: a817df9b4373
Revises: f0c540010d11
Create Date: 2026-11-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a817df9b4373'
down_revision: Union[str, Sequence[str], None] = 'f0c540010d11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        'ix_products_price_active',
        'products',
        ['price'],
        unique=False,
        postgresql_using='btree',
        postgresql_where='is_active = true',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_products_price_active', table_name='products')
