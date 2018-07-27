import random
import re
from datetime import datetime

from flask import abort, jsonify
from flask import current_app
from flask import json
from flask import make_response
from flask import request
from flask import session

from info import constants, db
from info import redis_store
from info.libs.yuntongxun.sms import CCP
from info.models import User

from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET

from .__init__ import passport_blu


@passport_blu.route('/imageCode')
def get_image_code():
    """
    １．获取查询参数
    ２．判断查询参数是否为空
    ３．不为空，则生成验证码并保存在redis中
    ４．生成验证码图片，返回给浏览器
    :return:
    """
    # 1.接收查询参数imageCodeId
    image_code_id=request.args.get('imageCodeId',None)
    # ２．判断查询参数是否为空
    if not image_code_id:
        abort(403)

    # ３．不为空，则生成验证码并保存在redis中
    name,text,image = captcha.generate_captcha()

    # 保存验证码内容，并设置失效时间
    try:
        redis_store.set('imageCodeId'+image_code_id,text,constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)

    # 创建响应并添加响应类型
    response=make_response(image)
    response.headers['Content-Type']='image/jpg'
    return response


@passport_blu.route('/sms_code',methods=['POST'])
def get_mesg_code():
    """
    1.接收手机号、图片验证码、随机值
    2.验证以上数据是否为空
    3.不为空，验证手机号格式是否正确
            验证图片验证码是否正确
    5.验证通过，生成短信验证码内容，发送给短信服务商
    6.短信是否发送成功，发送给浏览器对应的状态信息
    :return:
    """
    # 1.接收手机号、图片验证码、随机值
    # 这里接收的是json字符串数据，不是form表单数据
    # json字符串转换为字典，方便后续统一处理
    # print(request.data,type(request.data))

    param_dict=json.loads(request.data)
    # param_dict=request.json

    # print(param_dict)

    mobile=param_dict.get('mobile')
    image_code=param_dict.get('image_code')
    image_code_id=param_dict.get('image_code_id')

    # print(mobile,image_code,image_code_id)

    # 2.验证以上数据是否为空
    if not all([mobile,image_code,image_code_id]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不足')

    # 3.验证手机号格式是否正确
    if not re.match(r'1[3578]\d{9}',mobile):
        return jsonify(errno=RET.DATAERR,errmsg='手机号错误')

    # 点击获取手机验证码时，实现判断该手机号是否被注册的功能
    if User.query.filter(User.mobile==mobile).first():
        return jsonify(errno=RET.DATAEXIST,errmsg='该手机号已被注册')

    # 4.验证图片验证码是否正确
    try:
        real_image_code=redis_store.get('imageCodeId'+image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='数据库查询失败')

    # 5.验证查询到的数据是否为空
    if not real_image_code:
        return jsonify(errno=RET.NODATA,errmsg='验证码不存在')

    # 6.进行验证码对比:注意大小写和编码问题
    # print(real_image_code, image_code)
    # if image_code.upper() != real_image_code.upper().decode():
    # 也可在redis初始化时进行设置
    if image_code.upper() != real_image_code.upper():
        return jsonify(errno=RET.DATAERR,errmsg='验证码不正确')

    # 7.生成手机验证码--保存起来供后续验证用
    # mobile_code ={:0>6d}.format(random.randint(0,999999))
    mobile_code='%06d' % random.randint(0,999999)
    print('短信验证码是：%s' % mobile_code)
    try:
        redis_store.set('mobilbe'+mobile,mobile_code,constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='短信验证码保存失败')

    # 8.发送手机验证码到第三方平台
    result=CCP().send_template_sms(mobile,[mobile_code,constants.SMS_CODE_REDIS_EXPIRES/60],1)

    if result!=0:
        return jsonify(errno=RET.THIRDERR,errmsg='第三方系统错误')

    # 9.发送成功
    return jsonify(errno=RET.OK,errmsg='信息发送成功')


@passport_blu.route('/register',methods=['POST'])
def register():
    """
    注册逻辑：
    １．获取参数
    ２．校验参数
    ３．
    :return:
    """
    param_dict=json.loads(request.data)
    # param_dict=request.json

    mobile=param_dict.get('mobile')
    smscode=param_dict.get('smscode')
    password=param_dict.get('password')

    if not all([mobile,smscode,password]):
        return jsonify(errn=RET.PARAMERR,errmsg='参数错误')

    if not re.match(r'1[3578]\d{9}',mobile):
        return jsonify(errno=RET.DATAERR,errmsg='手机号错误')

    try:
        real_smscode=redis_store.get('mobilbe'+mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据库查询错误')

    if not real_smscode:
        return jsonify(errno=RET.NODATA,errmsg='短信验证码不存在或失效')

    if smscode!=real_smscode:
        return jsonify(errno=RET.DATAERR,errmsg='短信验证码输入错误')

    # 验证通过后，将用户数据保存到数据库中
    user=User()
    user.mobile=mobile
    # 昵称初始化为手机号
    user.nick_name=mobile
    # 记录最后一次登录信息
    user.last_login=datetime.now()
    # 密码要加密保存
    # 在模型定义中进行密码加密的实现
    # 使用@property装饰器和@password.setter装饰器实现对密码的加密
    user.password=password

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据异常')

    # 注册成功后，转为登录状态，将用户信息保存在session中
    session['user_id']=user.id
    session['mobile']=user.mobile
    session['nick_name']=user.nick_name

    # 返回注册成功状态
    return jsonify(errno=RET.OK,errmsg='数据保存成功')


@passport_blu.route('/login',methods=['POST'])
def login():
    """
    登录逻辑：
    １．接收参数
    ２．校验参数
    ３．查询数据库验证手机号
    4.验证密码是否正确
    5.保存登录状态
    记录最后一次登录时间
    ６．返回成功
    :return:
    """
    params=json.loads(request.data)
    params=request.json

    mobile=params.get('mobile')
    password=params.get('password')

    if not all([mobile,password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不足')

    if not re.match(r'1[3578]\d{9}',mobile):
        return jsonify(errno=RET.DATAERR,errmsg='手机号错误')

    try:
        user=User.query.filter(User.mobile==mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据库查询失败')

    if not user:
        return jsonify(errno=RET.USERERR,errmsg='用户不存在')

    # 验证密码是否正确
    if not user.check_password(password):
        return jsonify(errno=RET.PWDERR,errmsg='密码错误')

    session['mobile']=user.mobile
    session['user_id']=user.id
    session['nick_name']=user.nick_name

    # 记录最后一次登录时间，保存到数据库中
    user.last_login=datetime.now()

    # 另外一种实现方式：修改数据库，在每次请求完成之后自动提交
    # 设置SQLAlchemy相关配置项SQLALCHEMY_COMMIT_ON_TERADOWN=True
    # try:
    #     db.session.commit()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     db.session.rollback()

    return jsonify(errno=RET.OK,errmsg='登录成功')


@passport_blu.route('/logout')
def logout():
    # 清除session
    session.pop('user_id',None)
    session.pop('mobile',None)
    session.pop('nick_name',None)
    # 针对管理员账号登录后，进入新闻页，退出登录后，清除session；若不清除is_admin，则其他用户登录后也能访问管理员页面
    # !!!!!!!!!!!!!!!!!!!!
    session.pop('is_admin',None)

    return jsonify(errno=RET.OK,errmsg='退出成功')