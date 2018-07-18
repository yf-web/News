# 实现登录与注册相关的业务逻辑
from flask import Blueprint

# 所有路由都添加前缀/passport
passport_blu = Blueprint('passport', __name__,url_prefix='/passport')

from .views import *
