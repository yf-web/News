from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db, models
from info.models import User

# 定义配置文件类型
# create_app类似于工厂函数，根据参数传入的不同来创建不同的对象

app=create_app('development')

manager = Manager(app)

Migrate(app, db)
manager.add_command('db', MigrateCommand)


# 实现命令行创建管理用户功能
# 使用方法：命令行中输入：python main.py addsuperadmin -n xxxx -p yyyyy
@manager.option('-n',dest='name')
@manager.option('-p',dest='password')
def addsuperadmin(name,password):

    if not all([name, password]):
        print('参数不足')

    user=User()

    user.nick_name=name
    # mobile not null
    user.mobile=name
    user.password=password
    # 管理员
    user.is_admin=True

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)

    print('添加成功！')


if __name__ == "__main__":
    # print(app.url_map)
    manager.run()
