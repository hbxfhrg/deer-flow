"""Add free practice mode fields to scenes table

Revision ID: 20260519_add_free_practice_fields
Revises: 
Create Date: 2026-05-19 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260519_add_free_practice_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to scenes table for free practice mode
    op.add_column('scenes', sa.Column('practice_mode', sa.String(length=20), nullable=True, server_default='剧本式'))
    op.add_column('scenes', sa.Column('knowledge_base', sa.Text(), nullable=True))
    op.add_column('scenes', sa.Column('summary_text', sa.Text(), nullable=True))
    op.add_column('scenes', sa.Column('exam_categories', sa.String(length=200), nullable=True))
    op.add_column('scenes', sa.Column('scoring_rules', sa.Text(), nullable=True))
    # Update default value for difficulty from 'medium' to '简单'
    op.execute("UPDATE scenes SET difficulty = '简单' WHERE difficulty = 'medium'")


def downgrade() -> None:
    # Remove the new columns
    op.drop_column('scenes', 'practice_mode')
    op.drop_column('scenes', 'knowledge_base')
    op.drop_column('scenes', 'summary_text')
    op.drop_column('scenes', 'exam_categories')
    op.drop_column('scenes', 'scoring_rules')