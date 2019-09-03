from django.urls import path
from . import views

app_name = 'pinkproject'
urlpatterns = [
    path('', views.pinkproject, name='project'),
    path('all_projects', views.pinkproject, name='all'),
    path('create_project', views.create_project, name='create_project'),
    path('create_project/create', views.create, name='create')
]