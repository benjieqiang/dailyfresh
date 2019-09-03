from django.urls import path
from apps.order.views import OrderPlaceView,OrderCommitView,OrderPayView,CheckPayView,OrderCommentView
urlpatterns = [
    path('place/',OrderPlaceView.as_view(), name='place'),  # 订单页面
    path('commit/',OrderCommitView.as_view(), name='commit'),  # 订单创建
    path('pay/',OrderPayView.as_view(), name='pay'),  # 订单支付
    path('check/',CheckPayView.as_view(), name='check'),  # 支付查询
    path('comment/<str:order_id>',OrderCommentView.as_view(),name='comment'), #评论
]