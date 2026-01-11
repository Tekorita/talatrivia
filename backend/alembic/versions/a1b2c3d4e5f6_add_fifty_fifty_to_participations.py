"""add fifty_fifty to participations

Revision ID: a1b2c3d4e5f6
Revises: fbc42b345094
Create Date: 2025-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'fbc42b345094'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add fifty_fifty_used column
    op.add_column('participations', sa.Column('fifty_fifty_used', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add fifty_fifty_question_id column
    op.add_column('participations', sa.Column('fifty_fifty_question_id', UUID(as_uuid=True), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_participations_fifty_fifty_question_id',
        'participations',
        'questions',
        ['fifty_fifty_question_id'],
        ['id']
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint('fk_participations_fifty_fifty_question_id', 'participations', type_='foreignkey')
    
    # Drop columns
    op.drop_column('participations', 'fifty_fifty_question_id')
    op.drop_column('participations', 'fifty_fifty_used')

