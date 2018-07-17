from flask import Flask
# 可以用来设置session保存的位置
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis
from config import config

# 创建数据库对象，但不初始化app
# flask中的很多扩展都可以在创建对象时不初始化，后续通过init_app方法来进行初始化！！！！！！！！！！！1
db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__)

    # 添加配置
    # 虽然采用from config import config但config.py中的代码都跑了一遍，
    # 所以也能取到config['development']对应的类DevelopmentConfig
    # todo 怎么解释？
    app.config.from_object(config[config_name])

    # 初始化数据库对象
    db.init_app(app)

    # 初始化redis对象
    redis_store = StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT)

    # 开启CSRF
    CSRFProtect(app)

    # 设置session
    Session(app)

    return app
