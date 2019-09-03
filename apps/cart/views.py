from django.shortcuts import render,redirect,HttpResponse
from django.urls import reverse
from django.views import View
from django.http.response import JsonResponse
from apps.goods.models import  GoodsSKU
from django_redis import get_redis_connection
# Create your views here.
#添加数据到购物车 ajax
# 如果涉及到数据的修改（新增，更新，删除），采用post
# 如果只涉及数据的获取采用get

#/cart/add
class CartAddView(View):
    '''购物车记录添加'''
    def post(self,request):
        '''
        post请求方式添加购物车
        :param request:
        :return:
        '''
        #首先检验用户是否登录，如果未登录则跳转至登录页面
        user = request.user
        if not user.is_authenticated:
            #用户未登录
            return redirect(reverse('user:login'))
        #接受数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        #数据校验
        #1. 数据完整性
        if not all([sku_id,count]):
            return JsonResponse({"res":1,"errmsg":"数据不完整"})
        #2. 检验添加的商品数目
        try:
            count = int(count)
        except Exception as e:
            #商品数目出错
            return JsonResponse({"res":2,"errmsg":'商品数目出错'})
        #3. 检验商品是否存在
        try:
            sku= GoodsSKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({"res":3,"errmsg":"商品不存在"})
        #业务处理：添加购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id
        #先尝试获取sku_id的值 -》hget cart_key属性
        #如果sku_id在hash中不存在。hget返回None
        cart_count = conn.hget(cart_key,sku_id)
        if cart_count:
            #累加购物车中商品的数目
            count += int(cart_count)
        #检验商品的库存
        print(sku)
        if count > sku.stock:
            #库存不足
            return JsonResponse({'res':4,"errmsg":'商品库存不足'})

        #设置hash中sku_id对应的值
        conn.hset(cart_key,sku_id,count)

        #计算用户购物车中商品的条目数
        total_count = conn.hlen(cart_key)

        #返回应答
        return JsonResponse({'res':5,'total_count':total_count,'message':"添加成功"})

#/cart/
from utils.mixin import LoginRequiredMixin
class CartInfoView(LoginRequiredMixin,View):
    '''购物车页面显示'''
    def get(self,request):
        '''
        显示购物车页面
        :param request:
        :return:
        '''
        #获取登录的用户
        user = request.user

        #获取登录用户的购物车信息
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id

        #hgetall()返回一个字典，
        cart_dict = conn.hgetall(cart_key)

        skus = []
        total_count = 0
        total_price = 0
        #遍历获取商品的信息
        for sku_id,count in cart_dict.items():
            #根据商品的id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            #计算商品的小计
            amount = sku.price * int(count)
            # print('amounttype:',type(amount))
            #动态给sku对象加上一个属性amount,保存单个商品的总价
            sku.amount = amount
            # 动态给sku对象加上一个属性count,保存购物车中对应商品的数目
            sku.count = int(count)
            #添加
            skus.append(sku)
            #累加计算商品的总数目和总价格
            total_count += int(count)
            total_price += amount

        context = {
            'total_count': total_count,
            'total_price':total_price,
            'skus':skus
        }
        return render(request,'cart.html',context)

#/cart/update/
#更新购物车记录，采用ajax post,传递参数sku_id,count
class CartUpdateView(View):
    #更新购物车记录
    def post(self,request):

        #首先检验用户是否登录，如果未登录则跳转至登录页面
        user = request.user
        if not user.is_authenticated:
            #用户未登录
            return redirect(reverse('user:login'))
        #接受数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        print('前端发送的数据：',sku_id,count)
        #数据校验
        #1. 数据完整性
        if not all([sku_id,count]):
            return JsonResponse({"res":1,"errmsg":"数据不完整"})
        #2. 检验添加的商品数目
        try:
            count = int(count)
        except Exception as e:
            #商品数目出错
            return JsonResponse({"res":2,"errmsg":'商品数目出错'})
        #3. 检验商品是否存在
        try:
            sku= GoodsSKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({"res":3,"errmsg":"商品不存在"})
        #4. 检验商品库存
        if count > sku.stock:
            return JsonResponse({'res':4,'errmsg':'商品库存不足'})

        #业务处理
        conn = get_redis_connection('default')
        cart_key = "cart_%d"%user.id
        conn.hset(cart_key,sku_id,count)

        #计算用户购物车中的商品总件数{'1':5,'2':5} 。5+5 = 10
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)
        #返回应答
        return JsonResponse({'res':5,'total_count':total_count,'message':'更新成功'})

#删除购物车数据
#ajax post请求
#前端需要传递的参数，sku_id
#/cart/delete/
class CartDeleteView(View):
    '''购物车记录删除'''
    def post(self,request):
        '''
        post请求
        :param request:
        :return:
        '''
        #验证用户是否登录
        user = request.user
        if not user.is_authenticated:
            #用户未登录
            return JsonResponse({'res':1,'errmsg':'请先登录'})

        #接受数据
        sku_id = request.POST.get('sku_id')
        #校验数据
        if not sku_id:
            #数据不完整
            return JsonResponse({'res':2,'errmsg':'无效的商品id'})
        #检验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res':3,'errmsg':'商品不存在'})

        #业务处理：删除购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id
        #删除hdel
        conn.hdel(cart_key,sku_id)

        # 计算用户购物车中的商品总件数{'1':5,'2':5} 。5+5 = 10
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        #返回应答
        return JsonResponse({'res':4,'total':total_count,'message':'删除成功'})