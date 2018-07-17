from flask import Flask
# 可以用来设置session保存的位置
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis
from config import config

app = Flask(__name__)

# 添加配置
# 虽然采用from config import config但config.py中的代码都跑了一遍，
# 所以也能取到config['development']对应的类DevelopmentConfig
# todo 怎么解释？
app.config.from_object(config['development'])

# 数据库对象
db = SQLAlchemy(app)

# 初始化redis对象
redis_store = StrictRedis(host=config['development'].REDIS_HOST, port=config['development'].REDIS_PORT)

# 开启CSRF
CSRFProtect(app)

# 设置session
Session(app)
