from django.urls import path
from apps.user import views
from apps.user.views import RegisterView,ActiveView,LoginView,LogoutView,UserInfoView,UserOrderView,AddressView
from django.contrib.auth.decorators import login_required


urlpatterns = [
    # path('register/',views.register,name='register'),#用户注册
    path('register/',RegisterView.as_view(),name='register'),#用户注册
    path('active/<str:token>',ActiveView.as_view(),name='active'),#用户激活
    path('login/',LoginView.as_view(),name='login'),#用户登录
    path('logout/',LogoutView.as_view(),name='logout'),#用户登出
    # path('send/',views.send)#用户邮件测试

    #用户中心
    #利用login_required()可以实现
    # If the user isn't logged in, redirect to settings.LOGIN_URL, passing the current absolute path in the query string. Example: /accounts/login/?next=/polls/3/.
    # If the user is logged in, execute the view normally. The view code is free to assume the user is logged in.
    # path('',login_required(UserInfoView.as_view()),name='user'),#用户中心-信息页
    # path('order/',login_required(UserOrderView.as_view()),name='order'),#用户中心-订单页
    # path('address/',login_required(AddressView.as_view()),name='address'),#用户中心-地址页
    #使用LoginRequiredMixin类实现
    path('',UserInfoView.as_view(),name='user'),#用户中心-信息页
    path('order/<slug:page>',UserOrderView.as_view(),name='order'),#用户中心-订单页
    path('address/',AddressView.as_view(),name='address'),#用户中心-地址页


    #path('test/',views.user)
]
