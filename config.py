from redis import StrictRedis


# 配置类
class Config(object):

    # 配置数据库
    SQLALCHEMY_DATABASE_URI = 'mysql://root:74108520@127.0.0.1:3306/information'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 配置redis
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # 配置session
    SECRET_KEY = 'BnfxjsrMd92t3mzBmT76L/j2+NkmFcKERbKW9uO9MIEC0DgWe7R+sstQ=='
    # 指定session保存位置
    SESSION_TYPE = 'redis'
    # 指定目标redis
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 开启session标签
    SESSION_USE_SIGNER = True
    # 关闭session永久有效
    SESSION_PERMANENT = False
    # 设置过期时间:2天
    PERMANENT_SESSION_LIFETIME = 86400 * 2


class DevelopmentConfig(Config):
    """定义开发环境下的配置"""
    DEBUG = True


class ProductionConfig(Config):
    """定义生产环境下的配置"""
    DEBUG = False


class TestConfig(Config):
    """定义单元测试环境下的配置"""
    DEBUG = True


config={
    'development':DevelopmentConfig,
    'produciton':ProductionConfig,
    'testing':TestConfig
}