import time
from datetime import datetime

from flask import abort
from flask import current_app
from flask import g
from flask import redirect
from flask import render_template, jsonify
from flask import request
from flask import session
from flask import url_for

from info.models import User
from info.modules.admin import admin_blu
from info.utils.common import user_login_data
from info.utils.response_code import RET


@admin_blu.route('/login',methods=['GET','POST'])
def admin_login():
    """
    登录页面，不使用ajax
    :return:
    """
    if request.method=='GET':

        # 判断当前是否已经登录,若已登录，则重定向到管理员页面
        if session.get('user_id',None) and session.get('is_admin',False):
            return redirect(url_for('admin.admin_index'))

        return render_template('admin/login.html')

    user_name=request.form.get('username')
    password=request.form.get('password')

    if not all([user_name,password]):
        return render_template('admin/login.html',errmsg='参数不足')

    # 验证是否是管理员
    try:
        user_check=User.query.filter(User.nick_name==user_name,User.is_admin==True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html',errmsg='查询数据库异常')

    if not user_check:
        return render_template('admin/login.html',errmsg='管理员账号不存在')

    # 验证密码
    if not user_check.check_password(password):
        return render_template('admin/login.html',errmsg='密码错误')

    # 保存登录状态
    session['user_id'] = user_check.id
    # session['mobile'] = user_check.mobile
    session['nick_name'] = user_check.nick_name
    session['is_admin']=user_check.is_admin

    # 登录成功
    return redirect(url_for('admin.admin_index'))


@admin_blu.route('/index')
@user_login_data
def admin_index():
    """
    管理员页面
    :return:
    """
    user=g.user

    data={
        'user_info':user.to_dict()
    }
    return render_template('admin/index.html',data=data)


@admin_blu.route('/logout')
def admin_logout():
    """
    退出登录
    :return:
    """
    session.pop('user_id',None)
    session.pop('nick_name',None)
    session.pop('is_admin',None)

    return jsonify(errno=RET.OK, errmsg='退出成功')


@admin_blu.route('/user_count')
def user_count():

    total_count=0
    # 查询所有用户数量--不包括管理员
    try:
        total_count=User.query.filter(User.is_admin==False).count()
    except Exception as e:
        current_app.logger.error(e)
        abort(404)

    month_count=0
    # 查询本月注册用户数量
    # 本月第一天的格式要与数据库中保存的时间格式相同
    now=time.localtime()  # 获取本年本月
    # 将字符串转换为日期格式
    this_month_begin=datetime.strptime(('%d-%d-01' %(now.tm_year,now.tm_mon)),'%Y-%m-%d')  # 获取本年本月第一天
    try:
        month_count = User.query.filter(User.is_admin==False,User.create_time>=this_month_begin).count()
    except Exception as e:
        current_app.logger.error(e)
        abort(404)

    day_count=0
    # 查询当天注册用户数量
    this_day_begin = datetime.strptime(('%d-%d-%d' % (now.tm_year, now.tm_mon, now.tm_mday)), '%Y-%m-%d')  # 获取本年本月当天
    try:
        day_count = User.query.filter(User.is_admin==False,User.create_time>=this_day_begin).count()
    except Exception as e:
        current_app.logger.error(e)
        abort(404)

    data={
        'total_count': total_count,
        'month_count': month_count,
        'day_count': day_count
    }
    return render_template('admin/user_count.html',data=data)