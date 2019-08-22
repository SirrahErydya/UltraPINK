from django.urls import path
from . import views

app_name = 'som'
urlpatterns = [
    path('', views.som, name='som'),
    path('get_best_fits/<int:proto>/<int:n_fits>', views.get_best_fits, name='get_best_fits')
]