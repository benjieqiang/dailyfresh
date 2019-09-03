from django.db import models
from db.base_module import BaseModel
# from tinymce.models import HTMLField
# Create your models here.

class GoodsType(BaseModel):
    '''商品种类表:海鲜，肉类，蔬菜'''
    name = models.CharField(max_length=20,verbose_name='种类名称')
    logo = models.CharField(max_length=20,verbose_name='标识')
    image = models.ImageField(upload_to='./static/upload/type',verbose_name='商品类型图片')

    class Meta:
        db_table = 'df_goods_type'
        verbose_name_plural =  '商品种类'

    def __str__(self):
        return self.name

class GoodsSKU(BaseModel):
    '''商品库存量单位模型表'''
    status_choice = (
        (0,'下线'),
        (1,'上线'),
    )
    type = models.ForeignKey('GoodsType',verbose_name='商品种类',on_delete=models.CASCADE)
    goods = models.ForeignKey('GoodsSPU',verbose_name='商品SPU',on_delete=models.CASCADE)

    name = models.CharField(max_length=20,verbose_name='商品名称')
    desc = models.CharField(max_length=256,verbose_name='商品描述')
    price = models.DecimalField(max_digits=10, decimal_places=2,max_length=10,verbose_name='商品价格')
    unite = models.CharField(max_length=20,verbose_name='商品单位')
    image = models.ImageField(upload_to='./static/upload/goods',verbose_name='商品图片')
    stock = models.IntegerField(default=1,verbose_name='商品库存')
    sales = models.IntegerField(default=0,verbose_name='商品销量')
    status = models.SmallIntegerField(default=1,choices=status_choice,verbose_name='商品状态')
    #SmallIntegerField小整数，占用空间少。
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'df_goods_sku'
        verbose_name_plural = '商品SKU'


class GoodsSPU(BaseModel):
    '''商品SPU模型类：存储一些通用的概念'''
    name = models.CharField(max_length=20,verbose_name='商品SPU名称')
    detail = models.CharField(max_length=128,verbose_name='详情')

    class Meta:
        db_table = 'df_goods_spu'
        verbose_name_plural = '商品SPU'

    def __str__(self):
        return self.name

class GoodsImage(BaseModel):
    '''商品图片'''
    name = models.ForeignKey('GoodsSKU',verbose_name='商品',on_delete=models.CASCADE)
    image = models.ImageField(upload_to='./static/upload/goods',verbose_name="图片路径")


    class Meta:
        db_table = 'df_goods_image'
        verbose_name_plural = '商品图片'

class IndexGoodsBanner(BaseModel):
    '''首页轮播图：商品展示模型类'''
    sku = models.ForeignKey('GoodsSKU',verbose_name='商品',on_delete=models.CASCADE)
    image = models.ImageField(upload_to='./static/upload/banner',verbose_name='图片')
    index = models.SmallIntegerField(default=0,verbose_name='展示顺序')

    #当时报错了，利用_str_方法 return self.sku. self.sku不是一个字符串
    def __str__(self):
        return str(self.sku)

    class Meta:
        db_table = 'df_index_banner'
        verbose_name_plural = '首页轮播图'

class IndexPromotionBanner(BaseModel):
    '''首页促销活动模型类'''
    name = models.CharField(max_length=20,verbose_name='活动名称')
    url = models.URLField(verbose_name='活动链接')
    image = models.ImageField(upload_to='./static/upload/banner',verbose_name='活动图片')
    index = models.SmallIntegerField(default=0,verbose_name='展示顺序')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'df_index_promotion'
        verbose_name_plural = '主页促销活动'

class IndexTypeGoodsBanner(BaseModel):
    '''首页商品分类展示表'''
    display_type_choice = (
        (0,'文字'),
        (1,'图片'),
    )
    type = models.ForeignKey('GoodsType',verbose_name='商品类型',on_delete=models.CASCADE)
    sku = models.ForeignKey('GoodsSKU',verbose_name='商品SKU',on_delete=models.CASCADE)
    display_type = models.SmallIntegerField(default=1,choices=display_type_choice)
    index = models.SmallIntegerField(default=0,verbose_name='展示顺序')

    class Meta:
        db_table = 'df_index_type_goods'
        verbose_name_plural = '主页分类展示商品'

































































