from django.urls import path
from . import views

app_name = 'som'
urlpatterns = [
    path('', views.som, name='som'),
    path('get_best_fits/<int:n_fits>', views.get_best_fits_to_protos, name='get_best_fits_to_protos'),
    path('get_outliers/<int:n_fits>', views.get_outliers, name='get_outliers'),
    path('label/<slug:label>', views.label, name='label'),
    path('get_protos', views.get_protos, name='get_protos')
]