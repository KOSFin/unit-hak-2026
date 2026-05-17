"""add board admin settings

Revision ID: 0003_add_board_admin_settings
Revises: 0002_sync_schema_with_models
Create Date: 2026-05-17

"""

from alembic import op
import sqlalchemy as sa

revision = "0003_add_board_admin_settings"
down_revision = "0002_sync_schema_with_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    board_columns = [column["name"] for column in inspector.get_columns("boards")]

    if "owner_guest_id" not in board_columns:
        op.add_column("boards", sa.Column("owner_guest_id", sa.String(length=64), nullable=True))

    if "allow_guest_admin" not in board_columns:
        op.add_column(
            "boards",
            sa.Column("allow_guest_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        op.alter_column("boards", "allow_guest_admin", server_default=None)


def downgrade() -> None:
    op.drop_column("boards", "allow_guest_admin")
    op.drop_column("boards", "owner_guest_id")
