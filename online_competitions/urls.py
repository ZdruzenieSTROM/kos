

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('kos/', include('kos.urls'), name='kos'),
    path('mas-problem/', include('mas_problem.urls'), name='mas-problem')
]
