import random
import re

from flask import abort, jsonify
from flask import current_app
from flask import json
from flask import make_response
from flask import request

from info import constants
from info import redis_store
from info.libs.yuntongxun.sms import CCP

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
