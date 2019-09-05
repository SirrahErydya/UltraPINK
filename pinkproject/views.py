from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.core.exceptions import ObjectDoesNotExist
from pinkproject.models import Project
from som.models import SOM


def pinkproject(request, project_id=None):
    template = loader.get_template("pinkproject/project.html")
    no_template = loader.get_template("pinkproject/no_project.html")
    try:
        if project_id is None:
            current_project = Project.objects.get(current_project=True)
        else:
            current_project = Project.objects.get(id=project_id)
            load_project(current_project)
        soms = SOM.objects.filter(project=current_project)
        context = {
            # Pass some values from the backend here
            'current': current_project,
            'soms': soms
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
    load_project(project_model)
    return pinkproject(request)


def load_project(project):
    active_projects = Project.objects.filter(current_project=True)
    for pro in active_projects:
        pro.current_project = False
        pro.save()
    project.current_project = True
    project.save()

