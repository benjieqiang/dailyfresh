# -*- coding: utf-8 -*-
# Author:benjamin
# Date:
#名字固定
#定义索引类
from haystack import indexes
#1. 导入模型类
from apps.goods.models import GoodsSKU
#2. 指定对于某个类的某些数据建立索引
# 索引类名格式：模型类名+Index
class GoodsSKUIndex(indexes.SearchIndex,indexes.Indexable):
    #索引字段 use_template = True 指定根据表中的哪些字段建立索引文件的说明放在一个文件中
    text = indexes.CharField(document=True,use_template=True)

    def get_model(self):
        #返回模型类
        return GoodsSKU
    def index_queryset(self,using=None):
        #建立索引的数据
        return self.get_model().objects.all()