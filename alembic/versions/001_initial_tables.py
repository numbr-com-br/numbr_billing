"""Initial tables

Revision ID: 001_initial_tables
Revises: 
Create Date: 2025-01-06 20:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001_initial_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create plans table
    op.create_table('plans',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('asaas_id', sa.String(length=255), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=False),
    sa.Column('cycle', sa.String(length=50), nullable=False),
    sa.Column('features', sa.JSON(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('asaas_id')
    )
    op.create_index(op.f('ix_plans_id'), 'plans', ['id'], unique=False)

    # Create addons table
    op.create_table('addons',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('asaas_id', sa.String(length=255), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('asaas_id')
    )
    op.create_index(op.f('ix_addons_id'), 'addons', ['id'], unique=False)

    # Create customers table
    op.create_table('customers',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('asaas_id', sa.String(length=255), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('cpf_cnpj', sa.String(length=20), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('asaas_id'),
    sa.UniqueConstraint('cpf_cnpj'),
    sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_customers_id'), 'customers', ['id'], unique=False)

    # Create subscriptions table
    op.create_table('subscriptions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('asaas_id', sa.String(length=255), nullable=True),
    sa.Column('customer_id', sa.String(length=36), nullable=False),
    sa.Column('plan_id', sa.String(length=36), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('billing_type', sa.String(length=50), nullable=False),
    sa.Column('next_due_date', sa.Date(), nullable=True),
    sa.Column('value', sa.DECIMAL(precision=10, scale=2), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
    sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('asaas_id')
    )
    op.create_index(op.f('ix_subscriptions_customer_id'), 'subscriptions', ['customer_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_subscriptions_plan_id'), 'subscriptions', ['plan_id'], unique=False)

    # Create subscription_addons table
    op.create_table('subscription_addons',
    sa.Column('subscription_id', sa.String(length=36), nullable=False),
    sa.Column('addon_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['addon_id'], ['addons.id'], ),
    sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
    sa.PrimaryKeyConstraint('subscription_id', 'addon_id')
    )

    # Create payments table
    op.create_table('payments',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('asaas_id', sa.String(length=255), nullable=True),
    sa.Column('subscription_id', sa.String(length=36), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('billing_type', sa.String(length=50), nullable=False),
    sa.Column('value', sa.DECIMAL(precision=10, scale=2), nullable=False),
    sa.Column('net_value', sa.DECIMAL(precision=10, scale=2), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('paid_at', sa.DateTime(), nullable=True),
    sa.Column('invoice_url', sa.String(length=500), nullable=True),
    sa.Column('bank_slip_url', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('asaas_id')
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_subscription_id'), 'payments', ['subscription_id'], unique=False)

    # Create webhook_logs table
    op.create_table('webhook_logs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('event_type', sa.String(length=100), nullable=False),
    sa.Column('payment_id', sa.String(length=255), nullable=True),
    sa.Column('subscription_id', sa.String(length=255), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('raw_data', sa.JSON(), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_logs_id'), 'webhook_logs', ['id'], unique=False)
    op.create_index(op.f('ix_webhook_logs_payment_id'), 'webhook_logs', ['payment_id'], unique=False)
    op.create_index(op.f('ix_webhook_logs_subscription_id'), 'webhook_logs', ['subscription_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_webhook_logs_subscription_id'), table_name='webhook_logs')
    op.drop_index(op.f('ix_webhook_logs_payment_id'), table_name='webhook_logs')
    op.drop_index(op.f('ix_webhook_logs_id'), table_name='webhook_logs')
    op.drop_table('webhook_logs')
    op.drop_index(op.f('ix_payments_subscription_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_table('payments')
    op.drop_table('subscription_addons')
    op.drop_index(op.f('ix_subscriptions_plan_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_customer_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    op.drop_index(op.f('ix_customers_id'), table_name='customers')
    op.drop_table('customers')
    op.drop_index(op.f('ix_addons_id'), table_name='addons')
    op.drop_table('addons')
    op.drop_index(op.f('ix_plans_id'), table_name='plans')
    op.drop_table('plans')