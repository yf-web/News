# from flask import current_app
from flask import current_app, jsonify
from flask import render_template

from info import redis_store
from .__init__ import index_blu


@index_blu.route('/test')
def test():
    dic={
        'name':'yl',
        'age':12
    }
    return jsonify(dic)


@index_blu.route('/favicon.ico')
def favicon():
    # 当前应用－返回目标静态文件
    return current_app.send_static_file('news/favicon.ico')


@index_blu.route('/')
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

    return render_template('news/index.html')



