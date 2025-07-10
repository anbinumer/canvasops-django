from django.urls import path
from . import views

urlpatterns = [
    path('tool_selection/', views.tool_selection, name='tool_selection'),
    path('find_replace/', views.find_replace_tool, name='find_replace_tool'),
] 