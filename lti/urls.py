from django.urls import path
from . import views

urlpatterns = [
    # LTI 1.3 endpoints
    path('login/', views.login, name='lti_login'),
    path('launch/', views.launch, name='lti_launch'),
    path('jwks/', views.jwks, name='lti_jwks'),
    
    # Configuration endpoints
    path('configure/', views.configure, name='lti_configure'),
    path('xml/', views.xml_config, name='lti_xml_config'),
    
    # Tool interface
    path('tools/', views.tool_selection, name='tool_selection'),
    path('submission-review/', views.submission_review, name='lti_submission_review'),
    
    # Test endpoints
    path('iframe-test/', views.iframe_test, name='lti_iframe_test'),
    path('cookie-test/', views.cookie_test, name='lti_cookie_test'),
]