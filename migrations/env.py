import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context
import pymysql

# 因MySQLDB不支持Python3，使用pymysql扩展库代替MySQLDB库
pymysql.install_as_MySQLdb()

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')


def get_engine():
    try:
        app = current_app._get_current_object()
        return app.extensions['migrate'].db.get_engine(app)
    except RuntimeError:
        # 如果没有应用上下文，则使用配置创建引擎
        from flask import Flask
        import config
        
        temp_app = Flask(__name__)
        temp_app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/flask_demo?charset=utf8mb4'.format(
            config.username, config.password, config.db_address)
        temp_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        from flask_sqlalchemy import SQLAlchemy
        db = SQLAlchemy(temp_app)
        return db.get_engine()


def get_engine_url():
    try:
        app = current_app._get_current_object()
        return app.extensions['migrate'].db.get_engine(app).url
    except RuntimeError:
        # 如果没有应用上下文，则使用配置创建URL
        import config
        return 'mysql+pymysql://{}:{}@{}/flask_demo?charset=utf8mb4'.format(
            config.username, config.password, config.db_address)


# Add your model's MetaData object here
# for 'autogenerate' support
def get_metadata():
    try:
        app = current_app._get_current_object()
        db = app.extensions['migrate'].db
    except RuntimeError:
        # 如果没有应用上下文，则创建临时应用
        from flask import Flask
        import config
        
        temp_app = Flask(__name__)
        temp_app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/flask_demo?charset=utf8mb4'.format(
            config.username, config.password, config.db_address)
        temp_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        from flask_sqlalchemy import SQLAlchemy
        db = SQLAlchemy(temp_app)

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