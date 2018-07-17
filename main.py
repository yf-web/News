from flask import Flask, session
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis
# 可以用来设置session保存的位置
from flask_session import Session
from flask_migrate import Migrate,MigrateCommand


# 配置类
class Config(object):
    DEBUG=True
    # 配置数据库
    SQLALCHEMY_DATABASE_URI='mysql://root:74108520@127.0.0.1:3306/information'
    SQLALCHEMY_TRACK_MODIFICATIONS=False

    # 配置redis
    REDIS_HOST='127.0.0.1'
    REDIS_PORT=6379

    # 配置session
    SECRET_KEY='BnfxjsrMd92t3mzBmT76L/j2+NkmFcKERbKW9uO9MIEC0DgWe7R+sstQ=='
    # 指定session保存位置
    SESSION_TYPE='redis'
    # 指定目标redis
    SESSION_REDIS=StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    # 开启session标签
    SESSION_USE_SIGNER=True
    # 关闭session永久有效
    SESSION_PERMANENT=False
    # 设置过期时间:2天
    PERMANENT_SESSION_LIFETIME=86400*2


app = Flask(__name__)



# 添加配置
app.config.from_object(Config)

# 数据库对象
db=SQLAlchemy(app)

# 初始化redis对象
redis_store=StrictRedis(host=Config.REDIS_HOST,port=Config.REDIS_PORT)

# 开启CSRF
CSRFProtect(app)

# 设置session
Session(app)

manager=Manager(app)

Migrate(app,db)
manager.add_command('db',MigrateCommand)


@app.route('/')
def index():
    session['name']='hello'
    return 'index'


if __name__ == "__main__":
    manager.run()