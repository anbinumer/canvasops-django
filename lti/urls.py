from django.urls import path
from . import views

urlpatterns = [
    path('launch/', views.lti_launch, name='lti_launch'),
]