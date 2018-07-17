from logging.handlers import RotatingFileHandler
import logging
from flask import Flask
# 可以用来设置session保存的位置
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis
from config import config
from info.modules.index import index_blu


def setup_log(config_name):
    """配置log"""
    # 设置日志的记录等级
    logging.basicConfig(level=config[config_name].LOG_LEVEL)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


# 创建数据库对象，但不初始化app
# flask中的很多扩展都可以在创建对象时不初始化，后续通过init_app方法来进行初始化！！！！！！！！！！！1
db = SQLAlchemy()


def create_app(config_name):

    setup_log(config_name)

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

    # 注册index_blu
    app.register_blueprint(index_blu)

    return app
