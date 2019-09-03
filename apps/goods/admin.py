from django.contrib import admin
from apps.goods import models
# Register your models here.
from django.core.cache import cache
class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        '''新增或更新表中的数据时调用'''
        super().save_model(request, obj, form, change)

        # 发出任务让celery worker重新生成首页静态页
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        #清除首页的缓存；
        print('清除首页缓存...')
        cache.delete('index_data')

    def delete_model(self, request, obj):
        '''删除表中的数据时使用'''
        super().delete_model(request, obj)
        # 发出任务让celery worker重新生成首页静态页
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

#利用django.admin.ModelAdmin中save_model和delete_model重写方法
#首页促销活动admin动态修改
class IndexPromotionBannerAdmin(BaseModelAdmin):
    pass
#首页轮播图admin动态修改
class IndexGoodsBannerAdmin(BaseModelAdmin):
    pass
admin.site.register(models.GoodsType)
admin.site.register(models.IndexTypeGoodsBanner)
admin.site.register(models.GoodsSKU)
admin.site.register(models.GoodsSPU)
admin.site.register(models.GoodsImage)
admin.site.register(models.IndexPromotionBanner,IndexPromotionBannerAdmin)
admin.site.register(models.IndexGoodsBanner,IndexGoodsBannerAdmin)
