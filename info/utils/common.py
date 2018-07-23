# 自定义的工具类
import functools

from flask import current_app
from flask import g
from flask import session

from info.models import User


def index_to_class(index):
    if index==1:
        return 'first'
    if index==2:
        return 'second'
    if index==3:
        return 'third'
    return ''


# 对于在程序中多处使用的操作或变量，可以保存在g变量中
# 定义一个过滤器，用来查询并获取当前登录用户的信息，保存在ｇ变量中，
# 方便后续可以直接从g变量中提取

def user_login_data(f):
    # 其作用是保证被装饰函数的函数名不变
    # 如果不使用它，在flask中访问被装饰的函数时，
    # 函数名会变为wrapper(从装饰器的实现原理去理解)
    @functools.wraps(f)
    def wrapper(*args,**kwargs):
        user_id = session.get('user_id', None)

        user = None
        if user_id:
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)

        # 将登录的用户信息保存在g变量中
        g.user=user
        return f(*args,**kwargs)
    return wrapper
