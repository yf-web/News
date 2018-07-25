# 实现用户设置功能
from flask import Blueprint

# 所有路由都添加前缀/user
user_blu = Blueprint('user', __name__,url_prefix='/user')

from .views import *
