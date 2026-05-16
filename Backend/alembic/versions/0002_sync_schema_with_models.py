"""sync schema with current SQLAlchemy models

Revision ID: 0002_sync_schema_with_models
Revises: 0001_initial
Create Date: 2026-05-17

"""

from alembic import op
import sqlalchemy as sa

revision = "0002_sync_schema_with_models"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    def get_columns(table):
        return [c["name"] for c in inspector.get_columns(table)]

    def get_indexes(table):
        return [i["name"] for i in inspector.get_indexes(table)]

    def get_fks(table):
        return [f["name"] for f in inspector.get_foreign_keys(table)]

    # Boards columns
    boards_cols = get_columns("boards")
    if "public_id" not in boards_cols:
        op.add_column("boards", sa.Column("public_id", sa.String(length=32), nullable=True))
    if "image_path" not in boards_cols:
        op.add_column("boards", sa.Column("image_path", sa.String(length=500), nullable=True))
    if "retention_days" not in boards_cols:
        op.add_column("boards", sa.Column("retention_days", sa.Integer(), nullable=False, server_default="3"))
    if "expires_after_days" not in boards_cols:
        op.add_column("boards", sa.Column("expires_after_days", sa.Integer(), nullable=False, server_default="3"))
    if "last_activity_at" not in boards_cols:
        op.add_column("boards", sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    if "archived_at" not in boards_cols:
        op.add_column("boards", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))

    if "ix_boards_public_id" not in get_indexes("boards"):
        op.create_index("ix_boards_public_id", "boards", ["public_id"], unique=True)

    # Tasks columns
    tasks_cols = get_columns("tasks")
    if "correlation_id" not in tasks_cols:
        op.add_column("tasks", sa.Column("correlation_id", sa.String(length=64), nullable=True))
    if "guest_id" not in tasks_cols:
        op.add_column("tasks", sa.Column("guest_id", sa.String(length=64), nullable=True))

    tasks_indexes = get_indexes("tasks")
    if "ix_tasks_correlation_id" not in tasks_indexes:
        op.create_index("ix_tasks_correlation_id", "tasks", ["correlation_id"], unique=False)
    if "ix_tasks_guest_id" not in tasks_indexes:
        op.create_index("ix_tasks_guest_id", "tasks", ["guest_id"], unique=False)

    # Domain events columns
    de_cols = get_columns("domain_events")
    if "board_id" not in de_cols:
        op.add_column("domain_events", sa.Column("board_id", sa.String(length=36), nullable=True))
    if "correlation_id" not in de_cols:
        op.add_column("domain_events", sa.Column("correlation_id", sa.String(length=64), nullable=True))
    if "source" not in de_cols:
        op.add_column("domain_events", sa.Column("source", sa.String(length=50), nullable=True))

    de_fks = get_fks("domain_events")
    if "fk_domain_events_board_id_boards" not in de_fks:
        op.create_foreign_key("fk_domain_events_board_id_boards", "domain_events", "boards", ["board_id"], ["id"])

    de_indexes = get_indexes("domain_events")
    if "ix_domain_events_board_id" not in de_indexes:
        op.create_index("ix_domain_events_board_id", "domain_events", ["board_id"], unique=False)
    if "ix_domain_events_correlation_id" not in de_indexes:
        op.create_index("ix_domain_events_correlation_id", "domain_events", ["correlation_id"], unique=False)

    # Automation rules
    ar_cols = get_columns("automation_rules")
    if "board_id" not in ar_cols:
        op.add_column("automation_rules", sa.Column("board_id", sa.String(length=36), nullable=True))

    ar_fks = get_fks("automation_rules")
    if "fk_automation_rules_board_id_boards" not in ar_fks:
        op.create_foreign_key("fk_automation_rules_board_id_boards", "automation_rules", "boards", ["board_id"], ["id"])

    ar_indexes = get_indexes("automation_rules")
    if "ix_automation_rules_board_id" not in ar_indexes:
        op.create_index("ix_automation_rules_board_id", "automation_rules", ["board_id"], unique=False)

    # Notifications
    n_cols = get_columns("notifications")
    if "board_id" not in n_cols:
        op.add_column("notifications", sa.Column("board_id", sa.String(length=36), nullable=True))

    n_fks = get_fks("notifications")
    if "fk_notifications_board_id_boards" not in n_fks:
        op.create_foreign_key("fk_notifications_board_id_boards", "notifications", "boards", ["board_id"], ["id"])

    n_indexes = get_indexes("notifications")
    if "ix_notifications_board_id" not in n_indexes:
        op.create_index("ix_notifications_board_id", "notifications", ["board_id"], unique=False)

    # Incoming tasks
    it_cols = get_columns("incoming_tasks")
    if "board_id" not in it_cols:
        op.add_column("incoming_tasks", sa.Column("board_id", sa.String(length=36), nullable=True))

    it_fks = get_fks("incoming_tasks")
    if "fk_incoming_tasks_board_id_boards" not in it_fks:
        op.create_foreign_key("fk_incoming_tasks_board_id_boards", "incoming_tasks", "boards", ["board_id"], ["id"])

    it_indexes = get_indexes("incoming_tasks")
    if "ix_incoming_tasks_board_id" not in it_indexes:
        op.create_index("ix_incoming_tasks_board_id", "incoming_tasks", ["board_id"], unique=False)

    # Data migration for public_id (Postgres compatible)
    op.execute(
        """
        UPDATE boards
        SET public_id = md5(random()::text || id)
        WHERE public_id IS NULL
        """
    )
    op.alter_column("boards", "public_id", nullable=False)

    op.alter_column("boards", "retention_days", server_default=None)
    op.alter_column("boards", "expires_after_days", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_incoming_tasks_board_id", table_name="incoming_tasks")
    op.drop_constraint("fk_incoming_tasks_board_id_boards", "incoming_tasks", type_="foreignkey")
    op.drop_column("incoming_tasks", "board_id")

    op.drop_index("ix_notifications_board_id", table_name="notifications")
    op.drop_constraint("fk_notifications_board_id_boards", "notifications", type_="foreignkey")
    op.drop_column("notifications", "board_id")

    op.drop_index("ix_automation_rules_board_id", table_name="automation_rules")
    op.drop_constraint("fk_automation_rules_board_id_boards", "automation_rules", type_="foreignkey")
    op.drop_column("automation_rules", "board_id")

    op.drop_index("ix_domain_events_correlation_id", table_name="domain_events")
    op.drop_index("ix_domain_events_board_id", table_name="domain_events")
    op.drop_constraint("fk_domain_events_board_id_boards", "domain_events", type_="foreignkey")
    op.drop_column("domain_events", "source")
    op.drop_column("domain_events", "correlation_id")
    op.drop_column("domain_events", "board_id")

    op.drop_index("ix_tasks_guest_id", table_name="tasks")
    op.drop_index("ix_tasks_correlation_id", table_name="tasks")
    op.drop_column("tasks", "guest_id")
    op.drop_column("tasks", "correlation_id")

    op.drop_index("ix_boards_public_id", table_name="boards")
    op.drop_column("boards", "archived_at")
    op.drop_column("boards", "last_activity_at")
    op.drop_column("boards", "expires_after_days")
    op.drop_column("boards", "retention_days")
    op.drop_column("boards", "image_path")
    op.drop_column("boards", "public_id")
