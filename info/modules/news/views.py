from flask import abort, jsonify
from flask import current_app
from flask import g
from flask import render_template
from flask import request
from flask import session

from info import constants
from info.models import News, User
from info.modules.news import news_blu
from info.utils.common import user_login_data
from info.utils.response_code import RET


@news_blu.route('/<int:news_id>')
@user_login_data
def index(news_id):
    """
    新闻详情页
    :param news_id:
    :return:
    """
    # 获取新闻点击排行数据
    try:
        news_list=News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据出错')

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_review_dict())

    # 显示登录信息
    # 获取登录用户的信息，若没有登录，返回None
    user=g.user

    # 获取对应新闻详情页数据
    news=None
    try:
        news=News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        abort(404)

    # 更新新闻点击次数
    news.clicks+=1

    # 判断新闻是否被登录的用户收藏
    is_collected=False

    # 先判断用户是否登录
    if user:
        # 登录后再判断是否收藏
        if news in user.collection_news:
            is_collected=True

    data={
        'user_info':user.to_dict() if user else None,
        'news_dict_list':news_dict_list,
        'news':news.to_dict(),
        'is_collected':is_collected

    }
    return render_template('/news/detail.html',data=data)


@news_blu.route('/news_collect',methods=['POST'])
@user_login_data
def collect():
    """
    实现收藏操作
    :return:
    """
    # 先判断用户是否登录
    user=g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='用户未登录')

    # 接收参数
    # news_id=json.loads(request.data).get('news_id')
    news_id=request.json.get('news_id')
    action=request.json.get('action')

    # 校验参数
    if not all([news_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')

    try:
        news_id=int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    if action not in ['cancel_collect','collect']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 判断该新闻是否存在
    try:
        news=News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库异常')

    if not news:
        return jsonify(errno=RET.NODATA,errmsg='新闻不存在')

    # 判断是取消还是收藏
    if action=='collect':
        # 判断该新闻是否被收藏
        if news not in user.collection_news:
            user.collection_news.append(news)
    else:
        if news in user.collection_news:
            user.collection_news.remove(news)

    return jsonify(errno=RET.OK,errmsg='收藏/取消收藏成功')
