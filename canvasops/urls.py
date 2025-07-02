from django.urls import path
from . import views

urlpatterns = [
    path('config/', views.lti_config, name='lti_config'),
    path('login/', views.lti_login, name='lti_login'),
    path('launch/', views.lti_launch, name='lti_launch'),
    path('jwks/', views.lti_jwks, name='lti_jwks'),
    path('tools/', views.tool_selection, name='tool_selection'),
]