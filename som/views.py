from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from som.models import Prototype, Distance, SOM, Outlier, SomCutout
import som.som_analysis as sa


# Create your views here.
def som(request, project):
    template = loader.get_template("som/som.html")
    soms = SOM.objects.filter(project=project)
    active_som = soms.get(current=True)
    prototypes = Prototype.objects.filter(som=active_som).order_by('y', 'x')
    context = {
        # Pass some values from the backend here
        'prototypes': prototypes,
        'all_soms': soms,
        'active_som': active_som
    }
    return HttpResponse(template.render(context, request))


def get_best_fits(request, proto, n_fits=10):
    if proto != -1:
        best_fits = sa.get_best_fits(proto, n_fits)
        return JsonResponse({'best_fits': make_json(best_fits, n_fits), 'success': True})
    return JsonResponse({"success": False})


def get_best_fits_to_protos(request, n_fits=10):
    protos = request.POST.getlist('protos')
    cutouts = sa.get_best_fits_to_protos(protos, n_fits)
    return JsonResponse({'best_fits': make_json(cutouts, n_fits), "success": True})


def get_outliers(request, n_fits=10):
    outliers = Outlier.objects.all()[:n_fits]
    return JsonResponse({'best_fits': make_json(outliers, n_fits), 'success': True})


def make_json(imgs, n_fits):
    n = n_fits
    if n > len(imgs):
        n = len(imgs)
    best_fits = []
    for i in range(n):
        fit_i = {}
        fit_i['id'] = imgs[i].id
        fit_i['url'] = imgs[i].image.url
        fit_i['ra'] = imgs[i].ra
        fit_i['dec'] = imgs[i].dec
        best_fits.append(fit_i)
    return best_fits
