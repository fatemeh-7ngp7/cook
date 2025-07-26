# recipes/urls.py
from django.urls import path, re_path
from . import views

urlpatterns = [
    # صفحات اصلی
    path('', views.home, name='home'),
    path('recipes/', views.food_list, name='food_list'),
    #path('recipe/<slug:slug>/', views.food_recipe, name='food_recipe'),
    re_path(r'^recipe/(?P<slug>[\w\u0600-\u06FF-]+)/$', views.food_recipe, name='food_recipe'),
    # API endpoints
    path('api/toggle-like/', views.toggle_like, name='toggle_like'),
    path('api/search/', views.search_recipes, name='search_recipes'),
    path('api/filter/', views.filter_recipes, name='filter_recipes'),
]