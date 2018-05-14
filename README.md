# dingtalk-django-example

本项目使用django、celery、dingtalk-sdk开发 钉钉企业接入 和 ISV服务商接入 的demo。

项目初始化
----------
- 本项目依赖 mysql 和 redis 请先准备好相应环境
- 下载项目 `git clone https://github.com/007gzs/dingtalk-django-example.git`
- 创建配置文件 `example/local_settings.py` 参考 `example/local_settings.py.default` 进行配置
- 初始化项目 
```
# 安装依赖
pip install -r requirements.txt
# 初始化数据库
python manage.py makemigrations
python manage.py migrate
# 创建超管用户
python manage.py createsuperuser
# 在服务器上运行程序
sudo python manage.py runserver 0.0.0.0:80
```

ISV服务商开发配置
----------------
- 钉钉后台创建套件
- 登陆 `http://www.domain.com/admin/isv/suite/` 添加套件，填写相应信息
- 套件管理页面 回调URL 设置为 `http://www.domain.com/api/dingtalk/isv/suite/callback/你的套件Key`
- 测试微应用，主页地址填写为 `http://www.domain.com/static/microapp.html?appId=你的应用ID&corpId=$CORPID$` 

企业接入
--------
local_settings.py 中配置企业接入相关参数后 访问 `http://www.domain.com/api/dingtalk/corp/test/sync/corp` 可将企业员工同步到对应User表中，可以通过`http://www.domain.com/corp/user/`查看
