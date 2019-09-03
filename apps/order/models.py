from django.db import models
from db.base_module import *

# Create your models here.

class OrderInfo(BaseModel):
    '''订单信息模型类'''
    METHOD_CHOICE = {
        '0': '支付宝',
        '1': '微信支付',
        '2': '银联',
        '3': '货到付款',
    }
    PAY_METHOD_CHOICE = (
        (0,'支付宝'),
        (1,'微信支付'),
        (2,'银联'),
        (3,'货到付款'),
    )
    ORDER_STATUS = {
        1: '待支付',
        2: '待发货',
        3: '待收货',
        4: '待评价',
        5: '已完成',
    }
    STATUS_CHOICE = (
        (1,'待支付'),
        (2,'待发货'),
        (3,'待收货'),
        (4,'待评价'),
        (5,'已完成'),
    )
    order_id = models.CharField(max_length=128,primary_key=True,verbose_name='订单ID')
    user = models.ForeignKey('user.User',on_delete=models.CASCADE,verbose_name='用户')
    addr = models.ForeignKey('user.Address',on_delete=models.CASCADE,verbose_name='订单ID')
    pay_method = models.SmallIntegerField(default=PAY_METHOD_CHOICE,verbose_name='支付方式')
    total_count = models.IntegerField(default=1,verbose_name='商品数量')
    total_price = models.DecimalField(max_digits=10,decimal_places=2,verbose_name='总价')
    transit_price = models.DecimalField(max_length=32,verbose_name='运费',max_digits=10,decimal_places=2)
    order_status = models.SmallIntegerField(choices=STATUS_CHOICE,default=1,verbose_name='支付状态')
    trade_no = models.CharField(max_length=128,default='',verbose_name='支付编号')

    class Meta:
        db_table = 'df_order_info'
        verbose_name_plural = '订单信息'

class OrderGoods(BaseModel):
    '''订单商品表'''
    order = models.ForeignKey('OrderInfo',verbose_name='订单ID',on_delete=models.CASCADE)
    sku = models.ForeignKey('goods.GoodsSKU',verbose_name='商品SKU',on_delete=models.CASCADE)
    count = models.IntegerField(default=1,verbose_name='商品数量')
    price = models.DecimalField(max_digits=10,decimal_places=2,verbose_name='商品价格')
    comment = models.CharField(max_length=256,default='',verbose_name='评论')

    class Meta:
        db_table = 'df_order_goods'
        verbose_name_plural = '订单商品表'