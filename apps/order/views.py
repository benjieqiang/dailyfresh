from django.shortcuts import render,redirect
from django.urls import reverse
from django.http.response import JsonResponse
from apps.goods.models import  GoodsSKU
from apps.user.models import Address
from apps.order.models import *
from django_redis import get_redis_connection
from django.views import View
from django.db import transaction
from alipay import AliPay,ISVAliPay
from django.conf import settings
import os
# Create your views here.

#订单页面的显示
#post请求 /order/place/
class OrderPlaceView(View):
    '''提交订单页面的显示'''
    def post(self,request):
        '''
        接受前端用户提供的商品id列表
        :param request:
        :return:
        '''
        #获取登录的用户
        user = request.user

        #获取参数sku_ids
        sku_ids = request.POST.getlist('sku_ids')#['2','4','6']

        #校验数据
        if not sku_ids:
            #如果不存在，跳转至购物车页面
            return redirect(reverse('cart:show'))

        #redis请求
        conn = get_redis_connection('default')
        cart_key = "cart_%d"%user.id

        skus=[]
        total_count = 0
        total_price = 0
        #遍历sku_ids 获取用户要看购买的商品信息
        for sku_id in sku_ids:
            #根据商品的id获取商品的信息
            try:
                #商品是否存在
                sku = GoodsSKU.objects.get(id=sku_id)
            except Exception as e:
                return JsonResponse({"res": 1, "errmsg": "商品不存在"})

            #获取用户所有购买的商品的数目
            count = conn.hget(cart_key,sku_id)

            #计算商品的小计
            amount = sku.price * int(count)

            #动态给sku增加count属性用于保存购买商品的数目
            sku.count = int(count)
            #动态给sku增加amount,用于保存商品的小计
            sku.amount = amount
            #追加
            skus.append(sku)

            #累加计算商品的总件数和总价格
            total_count += int(count)
            total_price += amount

        #运费:实际开发时，属于一个子系统
        transit_price = 10

        #实付款
        total_pay = total_price + transit_price

        #获取用户的收件地址
        addrs = Address.objects.filter(user=user)

        #sku_ids
        sku_ids = ','.join(sku_ids) #[1,2,3]->1,2,3

        #组织上下文
        context = {
            'skus':skus,
            'total_count':total_count,
            'total_price':total_price,
            'transit_price':transit_price,
            'total_pay':total_pay,
            'addrs':addrs,
            'sku_ids':sku_ids,
        }

        #返回应答

        return render(request,'place_order.html',context)

#订单页面的提交
#ajax post请求，/order/commit/
#接受数据addr_id, pay_method, sku_ids
class OrderCommitView(View):
    #订单创建
    @transaction.atomic #使用atomic装饰函数
    def post(self,request):
        '''
        订单创建
        :param request:
        :return:
        '''
        #判断用户是否登录
        user = request.user
        if not  user.is_authenticated:
            #用户未登录
            return JsonResponse({"res":0,'errmsg':'用户未登录'})

        #接受数据
        addr_id= request.POST.get('addr_id')
        pay_method= request.POST.get('pay_method')
        sku_ids= request.POST.get('sku_ids') #4,5,3

        #校验参数
        if not all([addr_id,pay_method,sku_ids]):
            #参数不完整
            return JsonResponse({'res':1,'errmsg':'参数不完整'})

        #校验支付方式
        if pay_method not in OrderInfo.METHOD_CHOICE.keys():
            #不存在
            return JsonResponse({'res':2,'errmsg':'非法的支付方式'})

        #校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            #地址不存在
            return JsonResponse({'res':3,'errmsg':'地址不存在'})

        # todo:订单核心业务：

        # 组织参数：

        # 订单id：201901181007+用户id
        from datetime import datetime
        order_id = datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)
        #print(order_id)#201901181010408

        #运费：
        transit_price = 10

        #总数目和总价
        total_price = 0
        total_count = 0

        #设置事物保存点
        save_id = transaction.savepoint()

        try:
            # todo: 向df_order_info表中添加一条记录；
            order = OrderInfo.objects.create(
                order_id = order_id,
                user = user,
                addr = addr,
                pay_method = pay_method,
                total_count = total_count,
                total_price = total_price,
                transit_price = transit_price,
            )

            #todo: 用户订单有几个商品，就往df_order_goods中加入几条记录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d'%user.id
            sku_ids  = sku_ids.split(',') #1,3 -> [1,3]
            for sku_id in sku_ids:
                #获取商品的信息
                try:
                    # sku = GoodsSKU.objects.get(id = sku_id)
                    #悲观锁
                    #select * from df_goods_sku where id=sku_id for update;
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                    # print(type(sku))
                except GoodsSKU.DoesNotExist:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res':4,'errmsg':'商品不存在'})

                #事务结束后，锁才释放
                print('user:%d===stock:%d'%(user.id,sku.stock))
                import time
                time.sleep(10)

                #从redis中获取用户所有购买的商品的数目
                count = conn.hget(cart_key,sku_id)

                # todo:判断商品的库存：如果商品数目大于库存报错
                if int(count) > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res':7,'errmsg':'商品库存不足'})

                #todo:向df_order_goods表中添加一条记录
                OrderGoods.objects.create(
                    order = order,
                    sku = sku,
                    count = count,
                    price = sku.price,
                )

                #todo：更新商品的库存和销量
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()

                #todo:累加计算订单商品的总数量和总价格
                amount = sku.price * int(count)
                total_count += int(count)
                total_price += amount

            #todo:更新订单信息表中的商品的总价格和总数目
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res':6,'ermsg':'下单失败'})

        #提交事务
        transaction.savepoint_commit(save_id)

        #todo:清除用户购物车中对应的记录
        conn.hdel(cart_key,*sku_ids)


        return JsonResponse({'res':5,'message':'创建成功'})

#订单支付
#/order/pay/
class OrderPayView(View):
    #订单支付
    def post(self,request):
        #接受数据

        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res':1,'errmsg':'用户未登录'})

        #从前端获取order_id
        order_id = request.POST.get('order_id')

        #检验参数
        if not order_id:
            return JsonResponse({'res':2,'errmsg':"订单id不存在"})

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user = user,
                                          pay_method = 0,
                                          order_status = 1,
                                          )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res':3,'errmsg':"订单错误"})
        #业务处理（用户点击去付款，跳转至支付宝的沙箱付款页面）

        app_private_key_string = open(os.path.join(settings.BASE_DIR,'apps/order/app_private_key.pem')).read()
        alipay_public_key_string = open(os.path.join(settings.BASE_DIR,'apps/order/alipay_public_key.pem')).read()


        alipay = AliPay(
            appid="2016092300575592",
            app_notify_url=None,  # 默认回调url
            app_private_key_string = app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string = alipay_public_key_string,
            sign_type= "RSA2",  # RSA 或者 RSA2
            debug = True  # 默认False
        )
        # 如果你是 Python 3的用户，使用默认的字符串即可

        total_pay = order.total_price + order.transit_price #decimal

        print(total_pay)
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no= order_id,
            total_amount= str(total_pay), #支付总金额
            subject="天天生鲜%s"%order_id,
            return_url=None,
            notify_url=None,  # 可选, 不填则使用默认notify url
        )

        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        #返回应答

        return JsonResponse({'res':4,'pay_url':pay_url})

#获取交易结果
#/order/check/
class CheckPayView(View):
    #获取交易的结果
    def post(self, request):
        # 接受数据

        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 1, 'errmsg': '用户未登录'})

        # 从前端获取order_id
        order_id = request.POST.get('order_id')

        # 检验参数
        if not order_id:
            return JsonResponse({'res': 2, 'errmsg': "订单id不存在"})

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=0,
                                          order_status=1,
                                          )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': "订单错误"})
        # 业务处理（用户点击去付款，跳转至支付宝的沙箱付款页面）

        app_private_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem')).read()
        alipay_public_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem')).read()

        alipay = AliPay(
            appid = "2016092300575592",
            app_notify_url = None,  # 默认回调url
            app_private_key_string = app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string = alipay_public_key_string,
            sign_type = "RSA2",  # RSA 或者 RSA2
            debug = True  # 默认False
        )

        #调用支付宝的交易查询接口
        while True:
            response = alipay.api_alipay_trade_query(out_trade_no=order_id)

            '''
             response = {
                  "alipay_trade_query_response": {
                    "trade_no": "2017032121001004070200176844", #支付宝交易号
                    "code": "10000", #接口调用是否成功
                    "invoice_amount": "20.00",
                    "open_id": "20880072506750308812798160715407",
                    "fund_bill_list": [
                      {
                        "amount": "20.00",
                        "fund_channel": "ALIPAYACCOUNT"
                      }
                    ],
                    "buyer_logon_id": "csq***@sandbox.com",
                    "send_pay_date": "2017-03-21 13:29:17",
                    "receipt_amount": "20.00",
                    "out_trade_no": "out_trade_no15",
                    "buyer_pay_amount": "20.00",
                    "buyer_user_id": "2088102169481075",
                    "msg": "Success",
                    "point_amount": "0.00",
                    "trade_status": "TRADE_SUCCESS",
                    "total_amount": "20.00"
                  },
                  "sign": ""
                }
            '''
            print(response)
            code = response.get('code')
            trade_status = response.get('trade_status')

            #校验
            if code == '10000' and trade_status == 'TRADE_SUCCESS':
                #支付成功
                #获取支付宝交易号
                trade_no = response.get('trade_no')
                #更新订单状态
                order.trade_no = trade_no
                order.order_status = 4 #待评价
                order.save()
                #返回结果
                return JsonResponse({'res':4,'message':'支付成功'})
            elif  code == "40004" or (code == '10000' and trade_status == 'WAIT_BUYER_PAY'):
                #交易创建，等待买家付款
                import time
                time.sleep(5)
                continue
            else:
                #交易失败
                return JsonResponse({'res':5,'errmsg':'支付失败'})


#商品评论
#/order/comment/
class OrderCommentView(View):
    def get(self,request,order_id):
        #提供评论页面
        user = request.user

        #校验数据
        if not order_id:
            #返回订单页面
            return redirect(reverse('user:order'))
        try:
            #拿到订单数据
            order = OrderInfo.objects.get(order_id=order_id,user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse('user:order'))

        #根据订单状态获取订单的状态标题
        order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        #获取订单商品信息
        order_skus = OrderGoods.objects.filter(order_id=order_id)
        for order_sku in order_skus:
            #计算商品的小计
            amount = order_sku.count * order_sku.price
            #动态给order_sku加属性amount,保存商品小计
            order_sku.amount = amount
        #动态给order增加属性order_skus,保存订单商品信息
        order.order_skus = order_skus

        #使用模板
        return render(request,'order_comment.html',{'order':order})
    def post(self,request,order_id):
        #处理评论内容
        user = request.user
        # 校验数据
        if not order_id:
            # 返回订单页面
            return redirect(reverse('user:order'))
        try:
            # 拿到订单数据
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse('user:order'))

        #获取评论条数
        total_count = request.POST.get('total_count')
        total_count = int(total_count)

        for i in range(1,total_count+1):
            #获取评论的商品的id
            sku_id = request.POST.get('sku_%d'%i) #sku_1 sku_2 sku_3
            #获取评论的商品的内容
            content = request.POST.get('content_%d'%i,'')

            try:
                order_goods = OrderGoods.objects.get(order=order,sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5 #已完成
        order.save()

        return redirect(reverse("user:order",kwargs={'page':1}))




