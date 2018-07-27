# from flask import current_app
from flask import current_app, jsonify
from flask import g
from flask import render_template
from flask import request
from flask import session

from info import constants
from info import redis_store
from info.models import User, News, Category
from info.utils.common import user_login_data
from info.utils.response_code import RET
from .__init__ import index_blu


# @index_blu.route('/test')
# def test():
#     dic={
#         'name':'yl',
#         'age':12
#     }
#     return jsonify(dic)


@index_blu.route('/favicon.ico')
def favicon():
    # 当前应用－返回目标静态文件
    return current_app.send_static_file('news/favicon.ico')


@index_blu.route('/')
@user_login_data
def index():
    # logging模块输出日志信息
    # logging.debug('测试debug')
    # logging.warning('测试warning')
    # logging.error('测试error')
    # logging.fatal('测试fatal')

    # Flask自带的日志输出
    # current_app.logger.debug('测试debug')
    # current_app.logger.error('测试error')

    # 验证使用redis保存信息的功能
    # 补一个漏洞：蓝图什么时候用，什么时候导入，防止导入出问题
    # redis_store.set('name','yll')

    # 通过传入模板文件的数据内容不同来实现：
    # １．首页未登录状态显示
    # ２．实现登录状态显示

    # 首页登录完成后，重新加载页面，这时发送用户相关数据给前端
    # １．从session中取出用户数据
    # user_id=session.get('user_id',None)
    # user = None
    # if user_id:
    #
    #     try:
    #         user=User.query.get(user_id)
    #     except Exception as e:
    #         current_app.logger.error(e)
    user=g.user

    # 实现首页新闻点击排行
    # 查询新闻数据表，排序输出
    news_list=[]
    try:
        news_list=News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    news_dict_list=[]
    for new in news_list:
        news_dict_list.append(new.to_basic_dict())

    # 动态显示分类标题
    categories=Category().query.all()
    category_list=[]
    for category in categories:
        category_list.append(category.to_dict())

    # 接口数据最好采用字典形式传送
    data={
        # 三元表达式!!!!!!!!!!
        'user_info':user.to_dict() if user else None,
        'news_dict_list':news_dict_list,
        'category_list':category_list
    }

    return render_template('news/index.html',data=data)


# 实现首页新闻信息显示
@index_blu.route('/news_list')
def show_news():
    """
    获取前端请求的新闻分类及对应的新闻列表
    因为有新闻分类，所以新闻列表的获取单独出来发起请求
    :return:
    """
    cid=request.args.get('cid','1')
    page=request.args.get('page','1')
    per_page=request.args.get('per_page','10')

    try:
        cid=int(cid)
        page=int(page)
        per_page=int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')

    # 查询数据库
    filter_con=[News.status==0]
    if cid!=1:
        filter_con.append(News.category_id==cid)
    # 如果cid＝＝１查询所有数据，如果cid!=1按cid查询数据
    # 过滤条件存放在列表中，需要拆包!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    try:
        pagination=News.query.filter(*filter_con).order_by(News.create_time.desc()).paginate(page,per_page,False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据库查询错误')

    current_page=pagination.page
    total_page=pagination.pages
    page_content_list=pagination.items

    news_content_list=[]
    for new in page_content_list:
        news_content_list.append(new.to_basic_dict())

    data={
        'current_page':current_page,
        'total_page':total_page,
        'news_content_list':news_content_list
    }
    return jsonify(errno=RET.OK,errmsg='成功',data=data)