"""add reviews indexes

Revision ID: 4b3c063b8d47
Revises: 361d499638e0
Create Date: 2026-11-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '4b3c063b8d47'
down_revision: Union[str, Sequence[str], None] = '361d499638e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        'ix_reviews_product_id_created_at',
        'reviews',
        ['product_id', 'created_at'],
        unique=False,
        postgresql_using='btree',
    )
    op.create_index(
        'ix_reviews_product_id_rating',
        'reviews',
        ['product_id', 'rating'],
        unique=False,
        postgresql_using='btree',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_reviews_product_id_rating', table_name='reviews')
    op.drop_index('ix_reviews_product_id_created_at', table_name='reviews')
