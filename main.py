from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


# 配置类
class Config(object):
    DEBUG=True
    # 配置数据库
    SQLALCHEMY_DATABASE_URI='mysql://root:74108520@127.0.0.1:3306/information'
    SQLALCHEMY_TRACK_MODIFICATIONS=False


# 添加配置
app.config.from_object(Config)

db=SQLAlchemy(app,__name__)


@app.route('/')
def index():
    return 'index'


if __name__ == "__main__":
    app.run(debug=True)