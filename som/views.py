from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from som.models import Prototype, Distance, SOM, Outlier, SomCutout
import som.som_analysis as sa
import json
import sys, traceback


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


def get_protos(request):
    protos = sa.get_protos(json.loads(request.body)['protos'])
    json_protos = [prototype.to_json() for prototype in protos]
    return JsonResponse({'protos': json_protos, "success": True})


def get_best_fits_to_protos(request, n_fits=10):
    protos = json.loads(request.body)['protos']
    prototypes = sa.get_protos(protos)
    if len(protos) == 1:
        cutouts = sa.get_best_fits(protos[0], n_fits)
    else:
        cutouts = sa.get_best_fits_to_protos(prototypes, n_fits)
    json_cutouts = [cutout.to_json() for cutout in cutouts]
    return JsonResponse({'best_fits': json_cutouts, "success": True})


def label(request, label):
    data = json.loads(request.body)
    protos, cutouts = None, None
    if 'protos' in data.keys():
        protos = data['protos']
    if 'cutouts' in data.keys():
        cutouts = data['cutouts']
    try:
        if protos:
            sa.label_protos(protos, label)
            return JsonResponse({"success": True})
        if cutouts:
            sa.label_cutouts(cutouts, label)
            return JsonResponse({"success": True})
        return JsonResponse({"success": False})
    except:
        return JsonResponse({"success": False})


def get_outliers(request, n_fits=10):
    outliers = Outlier.objects.all()[:n_fits]
    json_outliers = [outlier.to_json() for outlier in outliers]
    return JsonResponse({'best_fits':  json_outliers, 'success': True})


def export_catalog(request, filename):
    data = json.loads(request.body)
    try:
        if 'ids' in data.keys():
            sa.export_catalog(data['ids'], filename)
        else:
            sa.export_catalog([], filename)
        return JsonResponse({'success': True})
    except:
        traceback.print_exc(file=sys.stdout)
        return JsonResponse({"success": False})
