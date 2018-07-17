import logging

from flask import current_app
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db

# 定义配置文件类型
# create_app类似于工厂函数，根据参数传入的不同来创建不同的对象
app=create_app('development')

manager = Manager(app)

Migrate(app, db)
manager.add_command('db', MigrateCommand)


if __name__ == "__main__":
    manager.run()
