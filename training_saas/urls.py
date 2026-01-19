from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    # Include institute URLs BEFORE admin to ensure custom URLs are matched first
    path('', include('institute.urls')),
    path('admin/', admin.site.urls),
    path('accounts/login/', RedirectView.as_view(url='/login/', permanent=False)),
    path('accounts/logout/', RedirectView.as_view(url='/logout/', permanent=False)),
]