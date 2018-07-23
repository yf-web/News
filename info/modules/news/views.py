from flask import abort, jsonify
from flask import current_app
from flask import g
from flask import render_template
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


    data={
        'user_info':user.to_dict() if user else None,
        'news_dict_list':news_dict_list,
        'news':news.to_dict()

    }
    return render_template('/news/detail.html',data=data)