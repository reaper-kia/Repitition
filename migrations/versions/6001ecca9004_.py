"""add visits table

Revision ID: 6001ecca9004
Revises: a0a836ffe07e
Create Date: 2026-09-09 19:33:58.273923

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '6001ecca9004'
down_revision: Union[str, None] = 'a0a836ffe07e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # ✅ ИСПРАВЛЕНО: Только создание таблицы visits. Никаких изменений в users!
    op.create_table(
        'visits',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('client_id', sa.UUID(), nullable=False),
        sa.Column('club_id', sa.UUID(), nullable=False),
        sa.Column('entered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('exited_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_visits_client_id'), 'visits', ['client_id'], unique=False)
    op.create_index('ix_visits_client_id_entered_at', 'visits', ['client_id', 'entered_at'], unique=False)
    op.create_index(op.f('ix_visits_club_id'), 'visits', ['club_id'], unique=False)
    op.create_index('ix_visits_club_id_exited_at', 'visits', ['club_id', 'exited_at'], unique=False)
    op.create_index(op.f('ix_visits_external_id'), 'visits', ['external_id'], unique=True)

def downgrade() -> None:
    # ✅ ИСПРАВЛЕНО: Чистый откат только для visits.
    op.drop_index(op.f('ix_visits_external_id'), table_name='visits')
    op.drop_index('ix_visits_club_id_exited_at', table_name='visits')
    op.drop_index(op.f('ix_visits_club_id'), table_name='visits')
    op.drop_index('ix_visits_client_id_entered_at', table_name='visits')
    op.drop_index(op.f('ix_visits_client_id'), table_name='visits')
    op.drop_table('visits')