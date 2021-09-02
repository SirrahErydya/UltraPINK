from django.http import HttpResponse
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
    data_lut = csv.reader(open(som.dataset.csv_path.path), delimiter=' ')
    header = []
    data = []
    for (i, row) in enumerate(data_lut):
        if i == 0:
            header = row
        if i == cutout.index:
            data = row
    cutout_meta = dict(zip(header, data))
    cutout_obj = cs.create_cutout_obj(cutout_meta, som, cutout)
    context = {
        'current': current_project,
        'projects': Project.objects.all(),
        'som': som,
        'cutout': cutout_obj,
        'cutout_meta': cutout_meta
    }
    return HttpResponse(template.render(context, request))
