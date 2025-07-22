from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='lti_login'),
    path('launch/', views.launch, name='lti_launch'),
    path('jwks/', views.jwks, name='lti_jwks'),
    path('cookie-test/', views.cookie_test, name='lti_cookie_test'),
]