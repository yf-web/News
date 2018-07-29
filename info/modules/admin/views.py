import time
from datetime import datetime, timedelta

from flask import abort
from flask import current_app
from flask import g
from flask import redirect
from flask import render_template, jsonify
from flask import request
from flask import session
from flask import url_for

from info import constants
from info.models import User, News
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
    """
    用户数据统计
    :return:
    """
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
    this_month_begin=datetime.strptime(('%d-%02d-01' %(now.tm_year,now.tm_mon)),'%Y-%m-%d')  # 获取本年本月第一天
    try:
        month_count = User.query.filter(User.is_admin==False,User.create_time>=this_month_begin).count()
    except Exception as e:
        current_app.logger.error(e)
        abort(404)

    day_count=0
    # 查询当天注册用户数量
    this_day_begin = datetime.strptime(('%d-%02d-%02d' % (now.tm_year, now.tm_mon, now.tm_mday)), '%Y-%m-%d')  # 获取本年本月当天
    try:
        day_count = User.query.filter(User.is_admin==False,User.create_time>=this_day_begin).count()
    except Exception as e:
        current_app.logger.error(e)
        abort(404)

    # 查询过去一个月(30days)中用户注册情况
    today_begin=datetime.strptime(datetime.now().strftime('%Y-%m-%d'),'%Y-%m-%d')  # 2018-07-29 00:00:00

    # 每一天的注册情况
    past_days=[]
    past_days_counts=[]
    for i in range(0,31):
        # timedelta()用来获得一段时间
        day_begin=today_begin-timedelta(i)
        next_day_begin=today_begin-timedelta(i-1)

        day_active_count=User.query.filter(User.is_admin==False,User.last_login>=day_begin,User.last_login<next_day_begin).count()

        past_days.append(day_begin.strftime('%Y-%m-%d'))  # 存储为字符串格式
        past_days_counts.append(day_active_count)

    past_days.reverse()
    past_days_counts.reverse()

    data={
        'total_count': total_count,
        'month_count': month_count,
        'day_count': day_count,
        'past_days':past_days,
        'past_days_counts':past_days_counts
    }
    return render_template('admin/user_count.html',data=data)


@admin_blu.route('/user_list')
def user_list():
    """
    获取用户列表信息
    :return:
    """
    current_page=request.args.get('p',1)
    try:
        current_page=int(current_page)
    except Exception as e:
        current_app.logger.error(e)
        current_page=1

    try:
        paginations=User.query.filter(User.is_admin==False).order_by(User.create_time.desc()).paginate(current_page,constants.ADMIN_USER_PAGE_MAX_COUNT)
        current_page=paginations.page
        total_pages=paginations.pages
        current_page_items=paginations.items
    except Exception as e:
        current_app.logger.error(e)

    user_dict_li=[]
    for user in current_page_items:
        user_dict_li.append(user.to_admin_dict())

    data={
        'current_page':current_page,
        'total_pages':total_pages,
        'user_dict_li':user_dict_li
    }

    return render_template('admin/user_list.html',data=data)


@admin_blu.route('/news_review')
def news_review():
    """
    待审核新闻列表
    :return:
    """
    current_page = request.args.get('p', 1)  # 接收页面信息
    keywords = request.args.get("keywords", "")  # 接收搜索信息
    try:
        current_page = int(current_page)
    except Exception as e:
        current_app.logger.error(e)
        current_page = 1

    filters=[News.status != 0]

    if keywords:
        filters.append(News.title.contains(keywords))  # 是否包含搜索字符串

    try:
        paginations = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(current_page,
                                                                                                           constants.ADMIN_USER_PAGE_MAX_COUNT)
        current_page = paginations.page
        total_pages = paginations.pages
        current_page_items = paginations.items
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = []
    for news in current_page_items:
        news_dict_li.append(news.to_review_dict())

    data = {
        'current_page': current_page,
        'total_pages': total_pages,
        'news_dict_li': news_dict_li
    }

    return render_template('admin/news_review.html',data=data)


@admin_blu.route('/news_review_details/<int:news_id>')  # 需要传入新闻id，方便获取新闻详细信息
def news_review_details(news_id):
    """
    待审核新闻信息编辑页
    :param news_id:
    :return:
    """

    news=None
    try:
        news=News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        abort(404)

    data={
        'news_info':news.to_dict()
    }

    return render_template('admin/news_review_detail.html',data=data)


@admin_blu.route('/news_review_action',methods=['POST'])
def news_review_action():
    """
    审核是否通过
    :return:
    """
    news_id=request.json.get('news_id',None)
    action=request.json.get('action',None)

    if not all([news_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数异常1')

    if action not in ['accept','reject']:
        return jsonify(errno=RET.PARAMERR,errmsg='参数异常2')

    try:
        news=News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据库异常')

    if not news:
        return jsonify(errno=RET.NODATA, errmsg='新闻不存在')

    # 审核通过
    if action=='accept':
        news.status=0

    # 审核不通过
    else:
        reason = request.json.get('reason', "")

        if not reason:
            return jsonify(errno=RET.PARAMERR,errmsg='原因不能为空')

        news.status = -1
        news.reason=reason

    return jsonify(errno=RET.OK, errmsg='成功')


@admin_blu.route('/news_edit')
def news_edit():
    """
    板式编辑列表
    :return:
    """
    current_page = request.args.get('p', 1)  # 接收页面信息
    keywords = request.args.get("keywords", "")  # 接收搜索信息
    try:
        current_page = int(current_page)
    except Exception as e:
        current_app.logger.error(e)
        current_page = 1

    filters=[News.status == 0]

    if keywords:
        filters.append(News.title.contains(keywords))  # 是否包含搜索字符串

    try:
        paginations = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(current_page,
                                                                                                           constants.ADMIN_USER_PAGE_MAX_COUNT)
        current_page = paginations.page
        total_pages = paginations.pages
        current_page_items = paginations.items
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = []
    for news in current_page_items:
        news_dict_li.append(news.to_basic_dict())

    data = {
        'current_page': current_page,
        'total_pages': total_pages,
        'news_dict_li': news_dict_li
    }

    return render_template('admin/news_edit.html',data=data)


@admin_blu.route('/news_edit_detail')
def news_edit_detail():
    return render_template('admin/news_edit_detail.html')