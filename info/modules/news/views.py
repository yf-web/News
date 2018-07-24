from flask import abort, jsonify
from flask import current_app
from flask import g
from flask import render_template
from flask import request
from flask import session

from info import constants, db
from info.models import News, User, Comment
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

    # 查询当前新闻下的评论信息
    comments=[]  # 下面的comments可能不存在，预定义一下
    try:
        comments=Comment.query.filter(Comment.news_id==news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库错误')

    comment_list=[]
    for comment in comments:
        comment_list.append(comment.to_dict())

    data={
        'user_info':user.to_dict() if user else None,
        'news_dict_list':news_dict_list,
        'news':news.to_dict(),
        'is_collected':is_collected,
        'comment_list':comment_list

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


@news_blu.route('/news_comment',methods=['POST'])
@user_login_data
def comment():
    """
    评论功能分析：
    １．评论新闻
    接收评论新闻的id、评论内容
    ２．评论其他用户的评论
    接收评论新闻的id、评论内容＋其他用户评论的id
    所以：同时实现评论新闻和评论其他用户的评论
    :return:
    """
    # 先判断用户是否登录
    user=g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='用户未登录')

    # 接收参数
    news_id=request.json.get('news_id')
    comment_content=request.json.get('comment')
    parent_id=request.json.get('parent_id')

    # 校验参数--parent_id可有可无
    if not all([news_id,comment_content]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误1')

    try:
        news_id=int(news_id)
        if parent_id:
            parent_id=int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误2')

    # 判断该新闻是否存在
    try:
        news=News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库异常')

    if not news:
        return jsonify(errno=RET.NODATA, errmsg='新闻不存在')

    # 保存评论内容
    comment=Comment()
    comment.news_id=news_id
    comment.content=comment_content
    comment.parent_id=parent_id
    comment.user_id=user.id

    #　这里为什么手动提交？因为返回数据中需要使用到提交的数据，如果依赖自动提交，评论数据是在请求完成之后提交的
    # 则无法获得提交的评论数据
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存数据异常')

    data={
        'comment':comment.to_dict()  # 该字典中的内容还包含user相关信息
    }
    return jsonify(errno=RET.OK,errmsg='评论成功',data=data)