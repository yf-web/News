from flask import Blueprint

admin_blu = Blueprint('admin', __name__,url_prefix='/admin')

from .views import *


# 定义请求钩子，限制用户登录权限
@admin_blu.before_request
def admin_limit():
    # 与新闻页的登录情况共同判断
    # 判断当前已登录的用户不是管理员,并且同时还请求链接到非管理员登录页面
    if not session.get('is_admin',False) and not request.url.endswith('/admin/login'):
        return redirect(url_for('admin.admin_login'))