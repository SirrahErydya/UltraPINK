from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from som.models import Prototype, Distance, SOM, Outlier, SomCutout


# Create your views here.
def som(request):
    template = loader.get_template("som/som.html")
    soms = SOM.objects.all()
    active_som = SOM.objects.get(training_dataset_name='UKIDSS_FIRST') # TODO: Remove hardcode
    prototypes = Prototype.objects.filter(som=active_som).order_by('y', 'x')
    context = {
        # Pass some values from the backend here
        'prototypes': prototypes,
        'all_soms': soms,
        'active_som': active_som
    }
    return HttpResponse(template.render(context, request))


def get_best_fits(request, proto, n_fits):
    if proto != -1:
        prototype = Prototype.objects.get(proto_id=proto)
        dists = Distance.objects.filter(prototype=prototype).order_by('distance')
        best_fits = make_json([dist.cutout for dist in dists], n_fits)
        return JsonResponse({'best_fits': best_fits, 'success': True})
    return JsonResponse({"success": False})


def get_outliers(request, n_fits):
    outliers = Outlier.objects.all()[:n_fits]
    json = make_json(outliers, n_fits)
    return JsonResponse({'best_fits': json, 'success': True})


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
