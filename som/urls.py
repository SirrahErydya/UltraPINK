from django.urls import path
from . import views

app_name = 'som'
urlpatterns = [
    path('', views.som, name='som'),
    path('add_som/<int:project_id>', views.add_som, name='add_som'),
    path('get_best_fits/<int:n_fits>', views.get_best_fits_to_protos, name='get_best_fits_to_protos'),
    path('get_outliers/<int:som_id>/<int:n_fits>', views.get_outliers, name='get_outliers'),
    path('label/<slug:label>', views.label, name='label'),
    path('export/<slug:filename>', views.export_catalog, name='export'),
    path('get_protos', views.get_protos, name='get_protos')
]