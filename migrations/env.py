import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')


def get_engine():
    app = current_app._get_current_object()
    return app.extensions['migrate'].db.get_engine(app)


def get_engine_url():
    app = current_app._get_current_object()
    return app.extensions['migrate'].db.get_engine(app).url


# Add your model's MetaData object here
# for 'autogenerate' support
def get_metadata():
    app = current_app._get_current_object()
    db = app.extensions['migrate'].db

    # Import all models to ensure they are registered
    from wxcloudrun import model  # 导入模型确保被识别
    
    return db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = get_engine_url()
    context.configure(
        url=url, target_metadata=get_metadata(), literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            process_revision_directives=process_revision_directives,
            **current_app.extensions['migrate'].configure_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()