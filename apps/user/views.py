from django.shortcuts import render,HttpResponse,redirect
from apps.user.models import *
from apps.goods.models import *
from apps.order.models import *
import re
from django.urls import reverse #反向解析
from django.views import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.conf import settings
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate, login,logout
from django.core.paginator import Paginator #获取分页

#未登录进行跳转
from utils.mixin import LoginRequiredMixin
# Create your views here.

# def register(request):
#     '''
#     注册处理
#     :param request:
#     :return:
#     '''
#     if request.method == 'GET':
#         #显示注册页面
#         return render(request,'register.html')
#     elif request.method == 'POST':
#         #注册处理；
#         #1.接受数据；
#         username = request.POST.get('user_name')
#         pwd = request.POST.get('pwd')
#         cpwd = request.POST.get('cpwd')
#         email = request.POST.get('email')
#         allow = request.POST.get('allow')
#         #2.校验数据；判断数据是否为空；
#         if not all([username,pwd,cpwd,email,allow]):
#             #数据不完整
#             return render(request,'register.html',{'errmsg':'数据不完整'})
#         #检验密码是否相同
#         if pwd != cpwd:
#             #密码不同
#             return render(request,'register.html',{'errmsg':'两次密码不同'})
#         #检验邮箱
#         #只允许英文字母、数字、下划线、英文句号、以及中划线组成
#         if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
#             return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
#         #允许
#         if allow != 'on':
#             return render(request,'register.html',{'errmsg':'请同意协议'})
#         #3.业务处理，先判断用户名是否重复，再将数据存入表中；
#         #检验用户名是否重复
#         try:
#             user = User.objects.get(username=username)
#         except User.DoesNotExist:
#             #用户名不存在
#             user = None
#         if user:
#             #用户名已存在
#             return render(request,'register.html',{'errmsg':'用户名已存在'})
#         else:
#             user = User.objects.create_user(username, email, pwd)
#             user.is_active = 0 #
#             user.save()
#             #4.返回应答，跳转至首页。
#             url = reverse('goods:index') #反向解析，去goods/index/
#         return redirect(url)
#         # return HttpResponse('register ok')

#CBV
class RegisterView(View):
    def get(self,request):
        # 显示注册页面
        return render(request, 'register.html')
    def post(self,request):
        # 注册处理；
        # 1.接受数据；
        username = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        cpwd = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 2.校验数据；判断数据是否为空；
        if not all([username, pwd, cpwd, email, allow]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        # 检验密码是否相同
        if pwd != cpwd:
            # 密码不同
            return render(request, 'register.html', {'errmsg': '两次密码不同'})
        # 检验邮箱
        # 只允许英文字母、数字、下划线、英文句号、以及中划线组成
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        # 允许
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
        # 3.业务处理，先判断用户名是否重复，再将数据存入表中；
        # 检验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None
        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
        else:
            user = User.objects.create_user(username, email, pwd)
            user.is_active = 0  #
            user.save()
            #发送激活邮件，包含激活链接http://127.0.0.1:8000/user/active/用户id
            #激活链接中需要包含用户的身份信息，并且把身份信息进行加密

            #加密用户的身份信息，生成激活的token
            serializer  = Serializer(settings.SECRET_KEY,3600)
            info = {'confirm':user.id}
            token = serializer.dumps(info) #bytes类型
            token = token.decode() #转为字符串
            # print(token)
            #发邮件,利用celery异步发邮件send_mail
            # 如果my_task函数有参数，可通过delay()传递,例如 my_task(a, b), my_task.delay(10, 20)
            send_register_active_email.delay(email,username,token) #发送激活信息
            # 4.返回应答，跳转至首页。
            url = reverse('goods:index')  # 反向解析，去goods/index/
            return redirect(url)
        # return HttpResponse('register ok')

class ActiveView(View):
    '''用户激活'''
    def get(self,request,token):
        '''
        进行用户的激活
        :param request:
        :return:
        '''
        #进行解密。获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY,3600)
        #过期报异常
        try:
            info = serializer.loads(token)
            user_id = info['confirm']
            print(user_id) #激活用户的id
            #根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1 #激活成功
            user.save()
            #跳转至登录页面
            return redirect(reverse('user:login'))
        except  SignatureExpired as e:
            #激活链接过期
            return HttpResponse('激活链接过期',e)

class LoginView(View):
    '''登录页面'''
    def get(self,request):
        #判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checkbox = 'on'
        else:
            username = ''
            checkbox = ''
        return render(request,'login.html',{'username':username,'checkbox':checkbox})

    def post(self,request):
        #接受数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        #print(username+':'+password)
        #校验数据
        #检验数据完整
        if not all([username,password]):
            return render(request,'login.html',{'status':'数据不完整'})
        #使用django内置的认证系统进行校验

        user = authenticate(username=username,password=password)
        print(user)
        if user is not None:
            #用户名和密码正确
            print('ok')

            if user.is_active:
                #用户已激活
                #记录用户的登录状态
                login(request,user)
                #获取登录后要跳转的地址
                #默认跳转至首页；
                next_url = request.GET.get('next',reverse('goods:index'))

                response = redirect( next_url)
                #记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    #记住用户名
                    response.set_cookie('username',username,max_age=7*24*3600)
                else:
                    response.delete_cookie('username')
                #跳转至首页
                return response
            else:
                #用户未激活
                return render(request,'login.html',{'status':'请激活你的账户'})
        else:
            #用户名或密码错误
            return render(request,'login.html',{'status':'用户名或密码错误'})

#/user/logout
class LogoutView(View):
    '''用户登出'''
    def get(self,request):
        logout(request)

        return redirect(reverse('goods:index'))

#/user/
class UserInfoView(LoginRequiredMixin,View):
    '''用户中心-信息页'''
    def get(self,request):
        '''
        显示
        :param request:
        :return:
        '''
        #如果用户未登录-》AnonymousUser类的一个实例
        #如果用户登录-》User类的一个实例
        #request.user.is_authenticated()
        #获取用户的个人信息
        user = request.user
        address = Address.objects.get_default_address(user)
        #获取用户的历史浏览记录,利用django_redis
        from django_redis import get_redis_connection
        con = get_redis_connection('default') #StrictRedis #default为settings里面的参数；

        history_key = 'history_%d'%user.id
        #获取用户最近浏览的5个商品；
        sku_ids = con.lrange(history_key,0,4)
        #从数据库中查询用浏览的5个商品的id
        #goods_li = GoodsSKU.objects.filter(id__in=sku_ids)

        # goods_res=[]
        # for a_id in sku_ids:
        #     for goods in goods_li:
        #         if a_id == goods.id:
        #             goods.res.append(goods)
        #
        #方法2 遍历获取用户浏览的商品信息；
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        #组织上下文
        context ={
            'page': 'user',
            'address': address,
            'goods_li':goods_li,
        }
        return render(request,'user_center_info.html',context)


#/user/order/
class UserOrderView(LoginRequiredMixin, View):
    '''用户中心-订单页'''
    def get(self, request,page):
        '''显示'''
        # 获取用户的订单信息
        user = request.user
        #获取该用户的订单信息
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')
        # print('order数据',orders)

        # 遍历获取订单商品的信息
        for order in orders:
            # 根据订单id获取商品信息 order 是一个对象OrderInfo object
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)
            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.count * order_sku.price
                # 动态给order_sku 增加属性amount，保存订单商品的小计
                order_sku.amount = amount

            # 动态给order增加属性，保存订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus

        # 分页
        # 对数据进行分页
        paginator = Paginator(orders, 1)

        # 获取第page页的内容,进行容错处理
        try:
            #数字
            page = int(page)
        except Exception as e:
            page = 1

        # 如果传送的页码大于总页码，就置1
        if page > paginator.num_pages:
            page = 1

        # 获取第page页的实例对象
        order_page = paginator.page(page) # <Page 9 of 17>
        # try:
        #     print(order_page.has_previous)
        #     print(order_page.has_next)
        # except Exception as e:
        #     print('报错')
        #Returns a Page object with the given 1-based index.
        # for order in order_page:
        #     for order_sku in order.order_skus:
        #         print(order_sku) # OrderGoods object (14)

        # 进行页码控制，页面上最多显示5个页码；
        # 分为4种情况：
        # 1. 总页数小于5，页面显示所有页码
        # 2. 如果当前页是前3页，显示1-5页；
        # 3. 如果当前页是后3页，显示后5页；
        # 5. 如果总页数减去当前页大于等于4，此时显示1-5页；
        # 4. 其他情况，显示当前页的前2页，当前页，当前页的后2页；
        num_pages = paginator.num_pages
        print('总页数:',num_pages)
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif num_pages <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        elif num_pages - page >= 4:
            pages = range(1, 6)
        else:
            pages = range(page - 2, page + 3)

        #组织上下文
        context ={
            'order_page':order_page,
            'pages':pages,
            'page':'order',
        }

        return render(request, 'user_center_order.html',context)
#/user/address
class AddressView(LoginRequiredMixin,View):
    '''用户中心-地址页'''
    def get(self,request):
        '''
        显示
        :param request:
        :return:
        '''
        #检验address是否存在默认地址
        user = request.user
        # try:
        #     address = Address.objects.get(user=user,is_default=True)
        # except Address.DoesNotExist:
        #     #不存在默认地址
        #     address = None
        address = Address.objects.get_default_address(user)
        return render(request,'user_center_site.html',{'page':'address','address':address})
    def post(self,request):
        '''接受数据，提交至数据库'''
        #1.接受数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        #2.进行校验
        #检验数据完整性
        if not all([receiver,addr,zip_code,phone]):
            return render(request,'user_center_site.html',{'errmsg':'数据不完整'})
        #检验手机合法性
        if re.match(phone,'^(13[0-9]|14[579]|15[0-3,5-9]|16[6]|17[0135678]|18[0-9]|19[89])\d{8}$'):
            return render(request,'user_center_site.html',{'errmsg':'手机格式不正确'})
        #3.业务处理
        #如果用户存在默认收货地址，添加的地址不作为默认收货地址，否则作为默认收货地址
        #获取登录用户对应User对象
        user = request.user
        # try:
        #     address = Address.objects.get(user=user,is_default=True)
        # except Address.DoesNotExist:
        #     #不存在默认地址
        #     address = None
        address = Address.objects.get_default_address(user)
        if address:
            #如果为真，添加的地址不作为默认地址；
            is_default = False
        else:
            is_default = True

        #添加地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        #4.返回应答
        return redirect(reverse('user:address'))




# #测试login_required
# from django.contrib.auth.decorators import login_required
# @login_required
# def user(request):
#     return render(request,'user_center_info.html')