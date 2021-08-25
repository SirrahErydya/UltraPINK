from django.urls import path
from . import views

app_name = 'cutouts'
urlpatterns = [
    path('cutout-view/<int:project_id>/<int:som_id>/<int:cutout_id>', views.cutout_view, name='cutout_view'),
    ]