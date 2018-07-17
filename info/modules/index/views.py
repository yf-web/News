# from flask import current_app

from .__init__ import index_blu


@index_blu.route('/index')
def index():
    # logging模块输出日志信息
    # logging.debug('测试debug')
    # logging.warning('测试warning')
    # logging.error('测试error')
    # logging.fatal('测试fatal')

    # Flask自带的日志输出
    # current_app.logger.debug('测试debug')
    # current_app.logger.error('测试error')

    return 'index222222'
