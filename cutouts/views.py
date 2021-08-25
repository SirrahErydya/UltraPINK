from django.http import HttpResponse
from django.template import loader
from pinkproject.models import Project
from som.models import SOM, DataPoint
from django.core.exceptions import ObjectDoesNotExist


# Create your views here.
def cutout_view(request, project_id, som_id, cutout_id):
    template = loader.get_template("cutouts/cutout-inspection.html")

    current_project = Project.objects.get(id=project_id)
    som = SOM.objects.get(id=som_id)
    cutout = DataPoint.objects.get(id=cutout_id)
    context = {
        'current': current_project,
        'projects': Project.objects.all(),
        'som': som,
        'cutout': cutout
    }
    return HttpResponse(template.render(context, request))

