import os
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls'))
]

if os.getenv('DJANGO_SETTINGS_MODULE') == 'config.settings.dev':
    import debug_toolbar
    urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
