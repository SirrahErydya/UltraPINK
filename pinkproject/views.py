from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from django.db.models import QuerySet
from django.core.exceptions import ObjectDoesNotExist
from pinkproject.models import Project, Dataset
from som.models import SOM, Prototype
from som.views import plot_image
import numpy as np


#from som.som_postprocessing import SOM as SOM_obj


def pinkproject(request, project_id, som_id=None):
    no_template = loader.get_template("pinkproject/no_project.html")
    try:
        current_project = Project.objects.get(id=project_id)
        datasets = Dataset.objects.filter(project=current_project)
        soms = QuerySet(SOM)
        for ds in datasets:
            soms = soms | SOM.objects.filter(dataset=ds)
        if som_id is not None:
            template = loader.get_template("pinkproject/project.html")
            active_som = SOM.objects.get(id=som_id)
            assert active_som.dataset.project.id == project_id
            prototypes = []
            if active_som:
                print("Som will be rendered")
                np_som = np.load(active_som.som_file.path)
                for y in range(active_som.som_height):
                    for x in range(active_som.som_width):
                        np_img = np_som[y][x]
                        print(np_img.shape)
                        prototypes.append(plot_image(np_img))
            context = {
                # Pass some values from the backend here
                'current': current_project,
                'active_som': active_som,
                'prototypes': prototypes,
            }
        else:
            template = loader.get_template("pinkproject/project_lander.html")
            context = {
                'current': current_project,
                'projects': Project.objects.all(),
                'datasets': datasets,
                'soms': soms,
            }
        return HttpResponse(template.render(context, request))

    except ObjectDoesNotExist:
        return HttpResponse(no_template.render({}, request))


def edit_project(request, project_id=None):
    context = {}
    if project_id is not None:
        context['project'] = Project.objects.get(id=project_id)
    template = loader.get_template("pinkproject/create_project.html")
    return HttpResponse(template.render(context, request))


def create_project(request, project_id=None):
    data = request.POST
    name = data['project-name']
    desc = data['project-desc']

    if project_id is None:
        project_model = Project(project_name=name, description=desc)
    else:
        project_model = Project.objects.get(id=project_id)
        project_model.project_name = name
        project_model.description = desc
    project_model.save()
    return redirect('pinkproject:project', project_id=project_model.id)



