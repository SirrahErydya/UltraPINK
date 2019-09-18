from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from som.models import Prototype, Distance, SOM, Outlier, SomCutout
import som.som_analysis as sa
import json
from django.core import serializers


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


def get_best_fits_to_protos(request, n_fits=10):
    protos = json.loads(request.body)['protos']
    prototypes = [Prototype.objects.get(proto_id=proto_id) for proto_id in protos]
    if len(protos) == 1:
        cutouts = sa.get_best_fits(protos[0], n_fits)
    else:
        cutouts = sa.get_best_fits_to_protos(prototypes, n_fits)
    json_cutouts = [cutout.to_json() for cutout in cutouts]
    json_protos = [prototype.to_json() for prototype in prototypes]
    return JsonResponse({'best_fits': json_cutouts, 'protos': json_protos, "success": True})


def label_prototypes(request, label):
    protos = json.loads(request.body)['protos']
    try:
        sa.label_protos(protos, label)
        return JsonResponse({"success": True})
    except:
        return JsonResponse({"success": False})


def get_outliers(request, n_fits=10):
    outliers = Outlier.objects.all()[:n_fits]
    return JsonResponse({'best_fits':  serializers.serialize('json', outliers), 'success': True})


