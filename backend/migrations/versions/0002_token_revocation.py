"""token revocation: token_blocklist + users.token_version

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'token_blocklist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('jti', sa.String(length=64), nullable=False),
        sa.Column('token_type', sa.String(length=10), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('token_blocklist', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_token_blocklist_expires_at'), ['expires_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_token_blocklist_jti'), ['jti'], unique=True)
        batch_op.create_index(batch_op.f('ix_token_blocklist_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('token_version', sa.Integer(), server_default='0', nullable=False)
        )


def downgrade():
    # ALTER direct (pas de batch) : la recréation de table SQLite perdrait
    # l'index fonctionnel uq_users_email_lower, non réfléchi par SQLAlchemy.
    op.drop_column('users', 'token_version')
    with op.batch_alter_table('token_blocklist', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_token_blocklist_user_id'))
        batch_op.drop_index(batch_op.f('ix_token_blocklist_jti'))
        batch_op.drop_index(batch_op.f('ix_token_blocklist_expires_at'))
    op.drop_table('token_blocklist')
