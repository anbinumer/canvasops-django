from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    return HttpResponse("CanvasOps Django LTI - Coming Soon!")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('lti/', include('lti.urls')),
    path('tools/', include('tools.urls')),
]