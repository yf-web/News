from flask import abort
from flask import current_app
from flask import make_response
from flask import request

from info import constants
from info import redis_store

from info.utils.captcha.captcha import captcha

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
