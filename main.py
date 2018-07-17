from flask import Flask, session
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis
# 可以用来设置session保存的位置
from flask_session import Session
from flask_migrate import Migrate, MigrateCommand
from config import Config

app = Flask(__name__)

# 添加配置
app.config.from_object(Config)

# 数据库对象
db = SQLAlchemy(app)

# 初始化redis对象
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

# 开启CSRF
CSRFProtect(app)

# 设置session
Session(app)

manager = Manager(app)

Migrate(app, db)
manager.add_command('db', MigrateCommand)


@app.route('/')
def index():
    return 'index'


if __name__ == "__main__":
    manager.run()
