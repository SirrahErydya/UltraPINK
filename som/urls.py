from django.urls import path
from . import views

app_name = 'som'
urlpatterns = [
    path('', views.som, name='som'),
    path('get_best_fits/<int:n_fits>', views.get_best_fits_to_protos, name='get_best_fits_to_protos'),
    path('get_outliers/<int:n_fits>', views.get_outliers, name='get_outliers'),
    path('label_protos/<slug:label>', views.label_prototypes, name='label_protos')
]