from django.db import models
from django.contrib.auth.models import AbstractUser
from db.base_module import  BaseModel
# Create your models here.

class User(AbstractUser,BaseModel):
    '''用户模型类'''
    class Meta:
        db_table = 'df_user'
        verbose_name_plural = '用户'

class AddressManager(models.Manager):
    '''自定义的模型管理类继承models.Manager'''
    #1. 改变原有查询的结果集：all()
    #2. 封装方法：用户模型类对应的数据表（增删改查）
    def get_default_address(self,user):
        '''获取用户默认的收获地址'''
        #self.model:获取self对象所在的模型类
        try:
            address = self.get(user=user, is_default=True)
        except self.model.DoesNotExist:
            # 不存在默认地址
            address = None

        return address


class Address(BaseModel):
    '''地址模型类'''
    user = models.ForeignKey('User',verbose_name='所属账户',on_delete=models.CASCADE)
    receiver = models.CharField(max_length=20,verbose_name='收件人')
    addr = models.CharField(max_length=256,verbose_name='收货地址')
    zip_code = models.CharField(max_length=6,null=True,verbose_name='邮编')
    phone = models.CharField(max_length=11,verbose_name='联系电话')
    is_default = models.BooleanField(default=False,verbose_name='是否默认')

    objects = AddressManager() #使用自定义的管理器对象
    class Meta:
        db_table = 'df_address'
        verbose_name_plural  = '地址'
