import os
import time
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import config
from config_manager import get_database_config

# 初始化web应用
app = Flask(__name__, instance_relative_config=True)

# 获取数据库配置
db_config = get_database_config()
app.config['DEBUG'] = config.DEBUG

# 根据环境配置设置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = db_config['SQLALCHEMY_DATABASE_URI']
app.config['TESTING'] = db_config['TESTING']

# 禁用SQLAlchemy的修改跟踪以避免警告
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化DB操作对象
db = SQLAlchemy(app)

# 现在再导入模型和视图，避免循环依赖
from wxcloudrun.model import Counters, User, CheckinRule, CheckinRecord  # noqa: F401
from wxcloudrun import views  # noqa: F401
from wxcloudrun.background_tasks import start_missing_check_service  # noqa: F401

# 加载配置
app.config.from_object('config')

# 加载控制器

try:
    with app.app_context():
        # 先尝试建立连接，再执行create_all
        # 这样可以确保连接可用后再执行数据库操作
        try:
            with db.engine.connect() as connection:
                pass  # 简单测试连接是否可用
        except Exception as connect_error:
            app.logger.warning(f"数据库连接测试失败: {str(connect_error)}")
            # 不要阻止应用启动，只是记录错误
            app.logger.error("无法连接到数据库，应用可能无法正常工作。")
        else:
            db.create_all()
            app.logger.info("数据库连接成功！")
            # 检查 Counters 表是否已创建
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            app.logger.info(f"数据库中已存在的表: {tables}")
            if 'Counters' not in tables:
                app.logger.warning("警告: Counters 表不存在")
            else:
                app.logger.info("Counters 表已存在")

            if 'users' in tables:
                cols = [c['name'] for c in inspector.get_columns('users')]
                migrations = []
                if 'is_solo_user' not in cols:
                    migrations.append(
                        "ALTER TABLE users ADD COLUMN is_solo_user INTEGER DEFAULT 1")
                if 'is_supervisor' not in cols:
                    migrations.append(
                        "ALTER TABLE users ADD COLUMN is_supervisor INTEGER DEFAULT 0")
                if 'is_community_worker' not in cols:
                    migrations.append(
                        "ALTER TABLE users ADD COLUMN is_community_worker INTEGER DEFAULT 0")
                if 'phone_hash' not in cols:
                    migrations.append(
                        "ALTER TABLE users ADD COLUMN phone_hash VARCHAR(64)")
                if 'password_hash' not in cols:
                    migrations.append(
                        "ALTER TABLE users ADD COLUMN password_hash VARCHAR(128)")
                if 'password_salt' not in cols:
                    migrations.append(
                        "ALTER TABLE users ADD COLUMN password_salt VARCHAR(32)")
                if migrations:
                    app.logger.info(f"对 users 表进行字段补全: {migrations}")
                    with db.engine.begin() as conn:
                        for sql in migrations:
                            conn.execute(text(sql))
                    app.logger.info("users 表字段补全完成")

            if 'checkin_rules' in tables:
                rule_cols = [c['name']
                             for c in inspector.get_columns('checkin_rules')]
                rule_migrations = []
                if 'custom_start_date' not in rule_cols:
                    rule_migrations.append(
                        "ALTER TABLE checkin_rules ADD COLUMN custom_start_date DATE")
                if 'custom_end_date' not in rule_cols:
                    rule_migrations.append(
                        "ALTER TABLE checkin_rules ADD COLUMN custom_end_date DATE")
                if rule_migrations:
                    app.logger.info(
                        f"对 checkin_rules 表进行字段补全: {rule_migrations}")
                    with db.engine.begin() as conn:
                        for sql in rule_migrations:
                            conn.execute(text(sql))
                    app.logger.info("checkin_rules 表字段补全完成")

            # supervision_rule_relations 邀请支持字段补齐
            if 'supervision_rule_relations' in tables:
                rel_cols = [c['name'] for c in inspector.get_columns(
                    'supervision_rule_relations')]
                rel_migrations = []
                # sqlite下将 supervisor_user_id 改为可空（如当前为NOT NULL则通过重建表迁移）
                try:
                    with db.engine.begin() as conn:
                        info = conn.execute(
                            text("PRAGMA table_info(supervision_rule_relations)")).fetchall()
                        notnull_map = {row[1]: row[3] for row in info}
                        if notnull_map.get('supervisor_user_id') == 1:
                            conn.execute(text("CREATE TABLE supervision_rule_relations_new (\n                                relation_id INTEGER PRIMARY KEY AUTOINCREMENT,\n                                solo_user_id INTEGER NOT NULL,\n                                supervisor_user_id INTEGER,\n                                rule_id INTEGER,\n                                status INTEGER DEFAULT 1,\n                                created_at TIMESTAMP,\n                                updated_at TIMESTAMP,\n                                invite_token VARCHAR(64),\n                                invite_expires_at TIMESTAMP\n                            )"))
                            conn.execute(text("INSERT INTO supervision_rule_relations_new (relation_id, solo_user_id, supervisor_user_id, rule_id, status, created_at, updated_at, invite_token, invite_expires_at)\n                                SELECT relation_id, solo_user_id, supervisor_user_id, rule_id, status, created_at, updated_at, invite_token, invite_expires_at FROM supervision_rule_relations"))
                            conn.execute(
                                text("DROP TABLE supervision_rule_relations"))
                            conn.execute(text(
                                "ALTER TABLE supervision_rule_relations_new RENAME TO supervision_rule_relations"))
                            conn.execute(text(
                                "CREATE INDEX IF NOT EXISTS idx_solo_supervisor ON supervision_rule_relations (solo_user_id, supervisor_user_id)"))
                            conn.execute(text(
                                "CREATE INDEX IF NOT EXISTS idx_supervisor_rule ON supervision_rule_relations (supervisor_user_id, rule_id)"))
                            conn.execute(text(
                                "CREATE UNIQUE INDEX IF NOT EXISTS idx_invite_token_unique ON supervision_rule_relations (invite_token)"))
                except Exception as e:
                    app.logger.warning(
                        f"迁移 supervision_rule_relations 以允许 supervisor_user_id 可空失败: {str(e)}")
                if 'invite_token' not in rel_cols:
                    rel_migrations.append(
                        "ALTER TABLE supervision_rule_relations ADD COLUMN invite_token VARCHAR(64)")
                if 'invite_expires_at' not in rel_cols:
                    rel_migrations.append(
                        "ALTER TABLE supervision_rule_relations ADD COLUMN invite_expires_at TIMESTAMP")
                # 修改 supervisor_user_id 允许为 NULL（仅在需要时）
                try:
                    with db.engine.begin() as conn:
                        conn.execute(text(
                            "ALTER TABLE supervision_rule_relations ALTER COLUMN supervisor_user_id DROP NOT NULL"))
                except Exception as e:
                    app.logger.warning(
                        f"修改supervisor_user_id为可空时出现异常，可能已是可空: {str(e)}")
                if rel_migrations:
                    app.logger.info(
                        f"对 supervision_rule_relations 表进行字段补全: {rel_migrations}")
                    with db.engine.begin() as conn:
                        for sql in rel_migrations:
                            conn.execute(text(sql))
                    app.logger.info("supervision_rule_relations 表字段补全完成")
except Exception as e:
    app.logger.error(f"数据库初始化失败: {str(e)}")
    app.logger.error("应用将继续启动，但数据库功能可能无法使用。")

# 启动后台missing标记服务
try:
    import os as _os
    # 仅在主进程中启动，避免debug模式下重复启动
    if _os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        start_missing_check_service()
except Exception as e:
    app.logger.error(f"启动后台missing服务失败: {str(e)}")
