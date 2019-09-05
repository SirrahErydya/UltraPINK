from django.urls import path
from . import views

app_name = 'pinkproject'
urlpatterns = [
    path('projects', views.pinkproject, name='project'),
    path('projects/<int:project_id>', views.pinkproject, name='project'),
    path('all_projects', views.pinkproject, name='all'),
    path('create_project', views.edit_project, name='create_project'),
    path('create_project/<int:project_id>', views.edit_project, name='create_project'),
    path('create_project/create/', views.create_project, name='create_new'),
    path('create_project/create/<int:project_id>', views.create_project, name='edit')
]