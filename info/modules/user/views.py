import errno

from flask import current_app
from flask import g, jsonify
from flask import redirect
from flask import render_template
from flask import request

from info import constants
from info import db
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
    return render_template('/news/user.html',data=data)


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
        return render_template('/news/user_base_info.html',data=data)


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
        return render_template('/news/user_pic_info.html',data=data)

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
