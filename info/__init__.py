from flask import Flask
# 可以用来设置session保存的位置
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis
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
