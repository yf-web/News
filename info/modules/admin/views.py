from flask import current_app
from flask import redirect
from flask import render_template, jsonify
from flask import request
from flask import session
from flask import url_for

from info.models import User
from info.modules.admin import admin_blu
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
def admin_index():

    return render_template('admin/index.html')