from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis
app = Flask(__name__)


# 配置类
class Config(object):
    DEBUG=True
    # 配置数据库
    SQLALCHEMY_DATABASE_URI='mysql://root:74108520@127.0.0.1:3306/information'
    SQLALCHEMY_TRACK_MODIFICATIONS=False

    # 配置redis
    REDIS_HOST='127.0.0.1'
    REDIS_PORT=6379


# 添加配置
app.config.from_object(Config)

# 数据库对象
db=SQLAlchemy(app)

# 初始化redis对象
redis_store=StrictRedis(host=Config.REDIS_HOST,port=Config.REDIS_PORT)

# 开启CSRF
CSRFProtect(app)


@app.route('/')
def index():
    return 'index'


if __name__ == "__main__":
    app.run(debug=True)