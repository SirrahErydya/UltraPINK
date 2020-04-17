from django.urls import path
from . import views

app_name = 'som'
urlpatterns = [
    path('create_som/<int:project_id>', views.save_som, name='create_som'),
    path('create_som/<int:project_id>/<int:dataset_id>', views.save_som, name='create_som'),
    path('add_som/<int:project_id>', views.add_som, name='add_som'),
    path('add_som/<int:project_id>/<int:dataset_id>', views.add_som, name='add_som'),
    path('map_protos/<int:som_id>', views.map_prototypes, name='map_protos'),
    path('get_best_fits/<int:n_fits>', views.get_best_fits_to_protos, name='get_best_fits_to_protos'),
    path('get_outliers/<int:som_id>/<int:n_fits>', views.get_outliers, name='get_outliers'),
    path('label/<slug:label>', views.label, name='label'),
    path('export/<slug:filename>', views.export_catalog, name='export'),
    path('get_protos', views.get_protos, name='get_protos')
]