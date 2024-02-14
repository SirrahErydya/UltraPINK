from django.http import HttpResponse, JsonResponse
from django.template import loader
from pinkproject.models import Project
from som.models import SOM, DataPoint
import csv
from . import cutout_spatial as cs
from django.core.exceptions import ObjectDoesNotExist


# Create your views here.
def cutout_view(request, project_id, som_id, cutout_id):
    template = loader.get_template("cutouts/cutout-inspection.html")

    current_project = Project.objects.get(id=project_id)
    som = SOM.objects.get(id=som_id)
    cutout = DataPoint.objects.get(id=cutout_id)
    cutout_meta = cutout.catalog_data()

    cutout_obj = cs.CutoutObj(cutout)
    context = {
        'current': current_project,
        'projects': Project.objects.all(),
        'som': som,
        'cutout': cutout_obj,
        'cutout_meta': cutout_meta
    }
    return HttpResponse(template.render(context, request))


def get_related_cutouts(request, cutout_id, n_cutouts=10):
    print("On my way to gather cutouts")
    cutout = DataPoint.objects.get(id=cutout_id)
    som = cutout.som
    cutout_obj = cs.CutoutObj(cutout)

    closest_cutouts = cs.cutout_distsort(cutout_obj, som)
    json_cutouts = []
    n = n_cutouts if len(closest_cutouts) > n_cutouts else len(closest_cutouts)
    for i in range(n):
        json_cut = closest_cutouts[i].to_dict()
        json_cut['distance'] = "%.2f" % cutout_obj.location.distance(closest_cutouts[i].location).degree
        json_cutouts.append(json_cut)

    print("Done!")
    return JsonResponse({'closest_cuts': json_cutouts, "success": True})


