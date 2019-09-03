from django.shortcuts import render,HttpResponse,redirect
from django.core.cache import cache
from django.views import View
from apps.goods.models import *
from apps.order.models import *
from django_redis import get_redis_connection
from django.urls import reverse
from django.core.paginator import Paginator #获取分页
# Create your views here.

#http://127.0.0.1:8000
class IndexView(View):
    '''首页'''
    def get(self,request):
        '''显示首页'''
        #首先从缓存中找到数据
        context = cache.get('index_data')
        if context is None:
            #设置缓存
            print('设置缓存')

            # 获取商品的种类信息
            types = GoodsType.objects.all()
            #print(types)
            #<QuerySet [<GoodsType: 新鲜水果>, <GoodsType: 猪牛羊肉>, <GoodsType: 新鲜蔬菜>, <GoodsType: 新鲜水果>, <GoodsType: 速冻食品>]>

            #获取首页轮播商品信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')
            #print(goods_banners)
            #<QuerySet [<IndexGoodsBanner: 维多利亚葡萄>, <IndexGoodsBanner: 草莓>, <IndexGoodsBanner: 猪肉>, <IndexGoodsBanner: 榨菜>]>

            #获取首页促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
            #print(promotion_banners)
            #<QuerySet [<IndexPromotionBanner: 双十一大促>, <IndexPromotionBanner: 双旦大促>]>

            #获取首页分类商品展示信息
            for type in types:
                print(type)
                #获取type种类首页分类商品的图片展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type,display_type=1)
                #获取type种类首页分类商品的文字展示信息
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type,display_type=0)

                #动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
                type.image_banners = image_banners
                type.title_banners = title_banners

            context = {
                'types': types,
                'goods_banners': goods_banners,
                'promotion_banners': promotion_banners,
            }
            cache.set('index_data',context,3600) #设置缓存，放置redis数据库中


        #获取用户购物车中商品的数目,从redis中动态获取
        user = request.user
        # print(user)
        cart_count = 0
        if user.is_authenticated:
            #用户已登录
            #将购物车记录添加至redis中；
            conn = get_redis_connection('default')
            cart_key = 'cart_%d'%user.id
            cart_count = conn.hlen(cart_key)

        context.update(cart_count=cart_count)
        #组织模板上下文

        return render(request,'index.html',context)

#/detail/商品id
class DetailView(View):
    '''商品详情页类'''
    def get(self,request,goods_id):
        '''
        显示商品详情页
        :param request:
        :param goods_id:
        :return:
        '''
        #先用goods_id去查询一下商品是否存在；
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
            # print('商品存在')
        except GoodsSKU.DoesNotExist:
            #商品不存在
            return redirect(reverse('goods:index'))
        #获取商品的分类信息
        types = GoodsType.objects.all()
        #获取商品的评论信息
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')
        # 获取新品信息,最新的新品
        print(sku.name,sku.desc,sku.image.url,sku.price,sku.unite)
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 获取同一个SPU的其他规格商品
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)
        print(same_spu_skus)
        for goods in same_spu_skus:
            print(goods.id)
        #获取购物车中商品的数目
        user = request.user
        # print(user)
        cart_count = 0
        if user.is_authenticated: # 用户已登录
            # 将购物车记录添加至redis中；
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

            #添加用户的历史记录
            conn = get_redis_connection('default')
            history_key = 'history_%d'%user.id
            #移除列表中的goods_id
            conn.lrem(history_key,0,goods_id)
            #把goods_id插入到列表的左侧
            conn.lpush(history_key,goods_id)
            #只保存用户最新浏览的5条信息
            conn.ltrim(history_key,0,4)

        #组织上下文
        context = {
            'sku':sku,
            'types':types,#分类信息
            'sku_orders':sku_orders, #获取评论信息
            'new_sku':new_skus, #新品信息
            'same_spu_skus':same_spu_skus,
            'cart_count':cart_count
        }

        return render(request,'detail.html',context)

#商品列表页：种类id,页码，排序方式
#/list/种类id/页码/排序方式
#/list/种类id/页码?sort=排序方式
class ListView(View):
    def get(self,request,type_id,page):
        #获取种类信息
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            #如果种类不存在，返回首页
            return redirect(reverse('goods:index'))

        #获取商品的分类信息
        types = GoodsType.objects.all()

        #先获取排序的方式，在获取分类商品的信息
        #sort = default,price,hot
        sort = request.GET.get('sort')
        if sort == 'price':
            #按照价格排序
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'hot':
            #按照热度排序
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            #按照默认排序
            sort ='default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # print('sku里的数据',skus)

        #获取分页信息from django.core.paginator import Paginator

        #对数据进行分页
        paginator = Paginator(skus,1)

        #获取第page页的内容,进行容错处理
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        #获取第page页的实例对象
        sku_page = paginator.page(page)
        for sku in sku_page:
            print(sku)

        # 进行页码控制，页面上最多显示5个页码；
        # 分为4种情况：
        #1. 总页数小于5，页面显示所有页码
        #2. 如果当前页是前3页，显示1-5页；
        #3. 如果当前页是后3页，显示后5页；
        #4. 其他情况，显示当前页的前2页，当前页，当前页的后2页；
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1,num_pages+1)
        elif num_pages <= 3:
            pages = range(1,6)
        elif num_pages - page <= 2:
            pages = range(num_pages-4,num_pages+1)
        else:
            pages = range(page-2,page+3)


        #获取新品信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 获取购物车中商品的数目
        user = request.user
        # print(user)
        cart_count = 0
        if user.is_authenticated:  # 用户已登录
            # 将购物车记录添加至redis中；
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        #组织上下文
        context = {
            'type':type,
            'types':types,
            'sku_page':sku_page,
            'new_skus':new_skus,
            'sort':sort,
            'pages':pages
        }
        return render(request,'list.html',context)