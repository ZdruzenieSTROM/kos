

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('kos/', include('kos.urls', namespace='kos')),
    path('mas-problem/', include('mas_problem.urls', namespace='mas-problem'))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
handler404 = 'kos.views.view_404'
