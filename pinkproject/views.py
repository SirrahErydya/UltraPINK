from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from django.db.models import QuerySet
from django.core.exceptions import ObjectDoesNotExist
from pinkproject.models import Project, Dataset
from som.models import SOM, Prototype
from som.views import som
import os
import shutil


#from som.som_postprocessing import SOM as SOM_obj


def pinkproject(request, project_id, som_id=None, view='proto'):
    no_template = loader.get_template("pinkproject/no_project.html")
    try:
        current_project = Project.objects.get(id=project_id)
        datasets = Dataset.objects.filter(project=current_project)
        soms = QuerySet(SOM)
        for ds in datasets:
            soms = soms | SOM.objects.filter(dataset=ds)
        if som_id is not None:
            return som(request, som_id, view)
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


def remove_som(request, som_id):
    som_model = SOM.objects.get(id=som_id)
    project_id = som_model.dataset.project.id
    som_path = os.path.join('projects', som_model.dataset.project.project_name, 'soms', som_model.som_name)
    shutil.rmtree(som_path, ignore_errors=True)
    som_model.delete()
    return redirect('pinkproject:project', project_id=project_id)


def remove_dataset(request, ds_id):
    ds_model = Dataset.objects.get(id=ds_id)
    project_id = ds_model.project.id
    dataset_path = os.path.join('projects', ds_model.project.project_name, 'datasets', ds_model.dataset_name)
    shutil.rmtree(dataset_path)
    soms = SOM.objects.filter(dataset=ds_model)
    for som_model in soms:
        som_path = os.path.join('projects', som_model.dataset.project.project_name, 'soms', som_model.som_name)
        shutil.rmtree(som_path, ignore_errors=True)
    ds_model.delete()
    return redirect('pinkproject:project', project_id=project_id)


