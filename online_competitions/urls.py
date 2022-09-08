

from django.contrib import admin
from django.contrib.flatpages.views import flatpage
from django.urls import include, path

urlpatterns = [
    path('/', flatpage, {'url': '/pravidla/'}, name='home'),
    path('admin/', admin.site.urls),
    path('kos/', include('kos.urls', namespace='kos')),
    path('mas-problem/', include('mas_problem.urls', namespace='mas-problem'))
]
handler404 = 'kos.views.view_404'
