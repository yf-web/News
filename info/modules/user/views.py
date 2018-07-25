from flask import g
from flask import redirect
from flask import render_template

from info.modules.user import user_blu
from info.utils.common import user_login_data


@user_blu.route('/info')
@user_login_data
def user_set():
    # 查询用户登录情况
    user=g.user
    # 如果没有登录则无法进入用户详情页,回到首页
    if not user:
        return redirect('/')

    data={
        'user_info':user.to_dict()
    }
    return render_template('/news/user.html',data=data)
