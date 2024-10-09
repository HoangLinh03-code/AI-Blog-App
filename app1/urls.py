from django.contrib import admin
from django.urls import path, include
from . import views
# from home import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login',views.login_user, name='login'),
    path('signup', views.signup, name='signup'),
    path('logout', views.logout_user, name= 'logout'),
    path('allblog', views.allblog, name='allblogs'),
    path('blogdetail', views.blog, name='blog'),
    path('generate-blog', views.generate_blog, name= 'generate-blog'),
    path('blog-list', views.blog_list, name='blog-list'),
    path('blog-detail/<int:pk>/', views.blog_detail, name='blog-detail')
]