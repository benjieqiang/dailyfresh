# -*- coding: utf-8 -*-
# Author:benjamin
# Date:
#使用celery实现异步执行任务
#我们将耗时任务放到后台异步执行。
#不会影响用户其他操作。除了注册功能，例如上传，图形处理等等耗时的任务
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail#发送邮件配置
from apps.goods.models import *
from django.shortcuts import render,HttpResponse
from django.template import loader
#在任务处理端加上django项目的初始化语句,避免报错
# import django
# import os
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
# django.setup()
#创建一个celery类的实例对象
app = Celery('celery_tasks.tasks',broker='redis://192.168.214.128:6379/8')
# from kombu import serialization
# serialization.registry._decoders.pop("application/x-python-serialize")
app.conf.update(
    CELERY_ACCEPT_CONTENT = ['json'],
    CELERY_TASK_SERIALIZER = 'json',
    CELERY_RESULT_SERIALIZER = 'json',
)


#定义一个任务函数
@app.task
def send_register_active_email(to_email,username,token):
    '''发送激活邮件'''
    #组织邮件信息

    subject = '天天生鲜注册信息'
    html_message = '<h1>%s,欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活你的账户<br/><a href="http://127.0.0.1:8000/user/active/%s"  target="_blank">点击激活</a>' % (
    username, token)
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    send_mail(subject, '', sender, receiver, html_message=html_message)
    import time
    time.sleep(10)

@app.task
def generate_static_index_html():
    '''
       显示首页：
       :param request:
       :return:
       '''
    # 获取商品的种类信息
    types = GoodsType.objects.all()
    # 获取首页轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')
    # #获取首页促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
    # 获取首页分类商品展示信息
    for type in types:
        # 获取type种类首页分类商品的图片展示信息
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1)
        # 获取type种类首页分类商品的文字展示信息
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0)

        # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
        type.image_banners = image_banners
        type.title_banners = title_banners


    # 组织模板上下文
    context = {
        'types': types,
        'goods_banners': goods_banners,
        'promotion_banners': promotion_banners,
    }
    #使用模板
    #1. 加载模板文件，返回模板对象
    temp = loader.get_template('static_index.html')
    #2. 定义模板上下文(省略)

    #3. 模板渲染
    static_index_html = temp.render(context)
    #生成首页对应静态文件
    import os
    save_path = os.path.join(settings.BASE_DIR,'static/index.html')
    with open (save_path,'w') as f:
        f.write(static_index_html)