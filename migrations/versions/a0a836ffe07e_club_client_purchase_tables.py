"""club_client_purchase_tables

Revision ID: a0a836ffe07e
Revises: 0001_initial
Create Date: 2026-09-09 16:13:56.118428

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a0a836ffe07e"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "reward_budgets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("club_id", sa.UUID(), nullable=False),
        sa.Column("budget_month", sa.Date(), nullable=False),
        sa.Column("revenue_base", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("configured_limit", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("reserved", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("spent", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("released", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("reserved + spent <= LEAST(configured_limit, revenue_base * 0.04)", name="ck_budget_limit"),
        sa.CheckConstraint("reserved >= 0 AND spent >= 0", name="ck_budget_non_negative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("club_id", "budget_month", name="uq_budget_club_month"),
    )
    
    op.create_table(
        "budget_reservations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("budget_id", sa.UUID(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("reserved_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("consumed_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("consumed_amount <= reserved_amount", name="ck_reservation_consumed"),
        sa.ForeignKeyConstraint(["budget_id"], ["reward_budgets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(op.f("ix_budget_reservations_budget_id"), "budget_reservations", ["budget_id"], unique=False)
    op.create_index(op.f("ix_budget_reservations_status"), "budget_reservations", ["status"], unique=False)
    
    op.create_table(
        "clubs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("manager_user_id", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["manager_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clubs_manager_user_id"), "clubs", ["manager_user_id"], unique=False)
    
    op.create_table(
        "clients",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("club_id", sa.UUID(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("membership_type", sa.String(length=32), nullable=False),
        sa.Column("membership_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("referral_code", sa.String(length=16), nullable=False),
        sa.Column("referred_by_client_id", sa.UUID(), nullable=True),
        sa.Column("acquisition_channel", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["referred_by_client_id"], ["clients.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("referral_code"),
    )
    op.create_index(op.f("ix_clients_club_id"), "clients", ["club_id"], unique=False)
    op.create_index(op.f("ix_clients_referred_by_client_id"), "clients", ["referred_by_client_id"], unique=False)
    op.create_index(op.f("ix_clients_status"), "clients", ["status"], unique=False)
    op.create_index(op.f("ix_clients_user_id"), "clients", ["user_id"], unique=True)
    
    op.create_table(
        "discount_grants",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("reservation_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("applicable_purchase_type", sa.String(length=32), nullable=False),
        sa.Column("source_key", sa.String(length=255), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["reservation_id"], ["budget_reservations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_key"),
    )
    op.create_index(op.f("ix_discount_grants_client_id"), "discount_grants", ["client_id"], unique=False)
    op.create_index(op.f("ix_discount_grants_status"), "discount_grants", ["status"], unique=False)
    
    op.create_table(
        "purchases",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("club_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("gross_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("confirmed_by_user_id", sa.UUID(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("discount_amount <= gross_amount", name="ck_purchases_discount_not_above_gross"),
        sa.CheckConstraint("discount_amount >= 0", name="ck_purchases_discount_amount_non_negative"),
        sa.CheckConstraint("gross_amount >= 0", name="ck_purchases_gross_amount_non_negative"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["confirmed_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(op.f("ix_purchases_client_id"), "purchases", ["client_id"], unique=False)
    op.create_index(op.f("ix_purchases_club_id"), "purchases", ["club_id"], unique=False)
    op.create_index(op.f("ix_purchases_confirmed_at"), "purchases", ["confirmed_at"], unique=False)

def downgrade() -> None:
    # ✅ ИСПРАВЛЕНО: Удален весь мусор про users. Откатываем только свои таблицы.
    op.drop_index(op.f("ix_purchases_confirmed_at"), table_name="purchases")
    op.drop_index(op.f("ix_purchases_club_id"), table_name="purchases")
    op.drop_index(op.f("ix_purchases_client_id"), table_name="purchases")
    op.drop_table("purchases")
    
    op.drop_index(op.f("ix_discount_grants_status"), table_name="discount_grants")
    op.drop_index(op.f("ix_discount_grants_client_id"), table_name="discount_grants")
    op.drop_table("discount_grants")
    
    op.drop_index(op.f("ix_clients_user_id"), table_name="clients")
    op.drop_index(op.f("ix_clients_status"), table_name="clients")
    op.drop_index(op.f("ix_clients_referred_by_client_id"), table_name="clients")
    op.drop_index(op.f("ix_clients_club_id"), table_name="clients")
    op.drop_table("clients")
    
    op.drop_index(op.f("ix_clubs_manager_user_id"), table_name="clubs")
    op.drop_table("clubs")
    
    op.drop_index(op.f("ix_budget_reservations_status"), table_name="budget_reservations")
    op.drop_index(op.f("ix_budget_reservations_budget_id"), table_name="budget_reservations")
    op.drop_table("budget_reservations")
    
    op.drop_table("reward_budgets")