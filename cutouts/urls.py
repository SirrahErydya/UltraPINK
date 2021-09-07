from django.urls import path
from . import views

app_name = 'cutouts'
urlpatterns = [
    path('cutout-view/<int:project_id>/<int:som_id>/<int:cutout_id>', views.cutout_view, name='cutout_view'),
    path('get_cutouts/<int:cutout_id>/<int:n_cutouts>', views.get_related_cutouts, name='get_cutouts'),
]