# cook/urls.py (main project urls)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('6@H61$h/', admin.site.urls),
    path('', include('recipe.urls')),
]

# اضافه کردن فایل‌های استاتیک و مدیا در حالت توسعه
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)