from django.urls import path,include
from apps.goods.views import IndexView,DetailView,ListView
urlpatterns = [
    path('index/',IndexView.as_view(),name='index'),#首页
    path('detail/<int:goods_id>',DetailView.as_view(),name='detail'),#商品详情页
    path('list/<int:type_id>/<int:page>',ListView.as_view(),name='list') #商品列表页

]