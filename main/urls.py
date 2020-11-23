import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('ludounadmin/', admin.site.urls),
    path('', include('ludoapp.urls')),
    path('moderator/', include('moderatorapp.urls')),
    path('accounts/logout/', auth_views.LogoutView.as_view()),
]

#urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
#urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
