import errno

from flask import current_app
from flask import g, jsonify
from flask import redirect
from flask import render_template
from flask import request

from info import constants
from info import db
from info.models import News, Category
from info.modules.user import user_blu
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET


@user_blu.route('/info')
@user_login_data
def user_set():
    """
    用户信息设置页
    :return:
    """
    # 查询用户登录情况
    user=g.user
    # 如果没有登录则无法进入用户详情页,回到首页
    if not user:
        return redirect('/')

    data={
        'user_info':user.to_dict()
    }
    return render_template('news/user.html',data=data)


@user_blu.route('/base_info',methods=['POST','GET'])
@user_login_data
def base_info():
    """
    用户基本信息页
    :return:
    """
    user=g.user

    if request.method=='POST':
        # 接收数据
        signature=request.json.get('signature')
        nick_name=request.json.get('nick_name')
        gender=request.json.get('gender')

        if not all([signature,nick_name,gender]):
            return jsonify(errno=RET.PARAMERR,errmsg='参数不能为空')

        if gender not in ['WOMAN','MAN']:
            return jsonify(errno=RET.PARAMERR,errmsg='参数错误')

        user.signature=signature
        user.nick_name=nick_name
        user.gender=gender

        return jsonify(errno=RET.OK,errmsg='成功')

    else:
        data={
            'user_info':user.to_dict()
        }
        return render_template('news/user_base_info.html',data=data)


@user_blu.route('/pic_info',methods=['POST','GET'])
@user_login_data
def user_pic_info():
    """
    修改用户头像
    :return:
    """
    user=g.user
    if request.method=='GET':

        data={
            'user_info':user.to_dict()
        }
        return render_template('news/user_pic_info.html',data=data)

    try:
        pic_file=request.files.get('avatar').read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='读取文件错误')
    try:
        key=storage(pic_file)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='第三方平台异常')

    # 保存图片在七牛中的相对路径，不完整
    user.avatar_url=key

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据异常')

    # 给前端返回图片的绝对地址,需要拼接为完整地址
    avatar_url=constants.QINIU_DOMIN_PREFIX+key
    data={
        'avatar_url':avatar_url
    }

    return jsonify(errno=RET.OK,errmsg='成功',data=data)


@user_blu.route('/pass_info',methods=['POST','GET'])
@user_login_data
def pass_info():
    if request.method=='GET':
        return render_template('news/user_pass_info.html')

    else:
        user=g.user
        old_password=request.json.get('old_password')
        new_password=request.json.get('new_password')

        if not all([old_password,new_password]):
            return jsonify(errno=RET.PARAMERR,errmsg='参数错误')

        if not user.check_password(old_password):
            return jsonify(errno=RET.PWDERR,errmsg='密码错误')

        user.password=new_password

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='数据库保存错误')

        return jsonify(errno=RET.OK,errmsg='成功')


@user_blu.route('/collection')
@user_login_data
def user_collection():
    """
    获取用户收藏的文章
    :return:
    """
    # 获取当前页数,如果没有穿值过来，默认显示第一页
    current_page=request.args.get('p',1)
    try:
        current_page=int(current_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='参数异常')

    # 查询当前用户收藏的文章
    user=g.user

    # 按时间排序分页
    paginations=user.collection_news.order_by(News.create_time.desc()).paginate(current_page,constants.USER_COLLECTION_MAX_NEWS)

    current_page=paginations.page
    total_page=paginations.pages
    current_page_news_li=paginations.items

    collection_news_li=[]
    for news in current_page_news_li:
        collection_news_li.append(news.to_review_dict())

    data={
        'current_page':current_page,
        'total_page':total_page,
        'collection_news_li':collection_news_li
    }

    return render_template('news/user_collection.html',data=data)


@user_blu.route('/news_release',methods=['GET','POST'])
@user_login_data
def news_release():
    """
    用户发布或修改新闻内容功能
    :return:
    """
    # 发给前端新闻分类数据
    if request.method=='GET':
        try:
            categories=Category.query.filter(Category.id!=1).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='查询数据库异常')

        category_li=[]
        for category in categories:
            category_li.append(category.to_dict())

        data={
            'categories':category_li
            }
        return render_template('news/user_news_release.html',data=data)

    # 接收用户新闻文章信息
    else:
        user=g.user
        title=request.form.get('title')
        source='个人发布'
        category_id=request.form.get('category_id')
        # 摘要
        digest=request.form.get('digest')
        index_image=request.files.get('index_image')
        content=request.form.get('content')

        if not all([title,category_id,digest,index_image,content]):
            return jsonify(errno=RET.PARAMERR,errmsg='参数异常１')

        try:
            category_id=int(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR,errmsg='参数异常２')

        # 转换数据格式，并将图片保存在七牛上
        try:
            key = index_image.read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg='数据异常３')

        try:
            key = storage(index_image)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg='第三方平台异常')

        # 保存新闻数据到News()数据表中
        news=News()
        news.title=title
        news.digest = digest
        news.source = source
        news.content = content
        # 保存图片路径，绝对路径：因为爬来的文章图片是全路径，自己的发布的文章也用全路径，好统一处理
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
        news.category_id = category_id
        news.user_id=user.id
        news.status=1

        try:
            db.session.add(news)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='保存数据异常')

        return jsonify(errno=RET.OK,errmsg='成功')


@user_blu.route('/news_list')
@user_login_data
def news_list():
    """
    显示用户发布的新闻列表
    :return:
    """
    current_page=request.args.get('p',1)

    try:
        current_page = int(current_page)
    except Exception as e:
        current_app.logger.error(e)
        current_page = 1

    try:
        pagination=News.query.filter(News.user_id==g.user.id).paginate(current_page,constants.USER_RELEASE_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库异常')

    total_page=pagination.pages
    news_li=pagination.items
    current_page=pagination.page

    news_status_li=[]
    for news in news_li:
        news_status_li.append(news.to_review_dict())

    data={
        'current_page':current_page,
        'total_page':total_page,
        'news_status_li':news_status_li
    }

    return render_template('news/user_news_list.html',data=data)