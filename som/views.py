from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from som.models import Prototype, Distance, SOM


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
        n = n_fits
        if n > len(dists):
            n = len(dists)
        best_fits = []
        for i in range(n):
            fit_i = {}
            fit_i['id'] = dists[i].cutout.id
            fit_i['url'] = dists[i].cutout.image.url
            fit_i['ra'] = dists[i].cutout.ra
            fit_i['dec'] = dists[i].cutout.dec
            best_fits.append(fit_i)
        return JsonResponse({'best_fits': best_fits, 'success': True})
    return JsonResponse({"success": False})
