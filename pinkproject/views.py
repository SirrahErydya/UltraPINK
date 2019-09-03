from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.core.exceptions import ObjectDoesNotExist
from pinkproject.models import Project
from som.models import  SOM


def pinkproject(request):
    template = loader.get_template("pinkproject/project.html")
    no_template = loader.get_template("pinkproject/no_project.html")
    try:
        current_project = Project.objects.get(current_project=True)
        soms = SOM.objects.filter(project=current_project)
        context = {
            # Pass some values from the backend here
            'current': current_project,
            'soms': soms
        }
        return HttpResponse(template.render(context, request))
    except ObjectDoesNotExist:
        return HttpResponse(no_template.render({}, request))


def create_project(request):
    template = loader.get_template("pinkproject/create_project.html")
    return HttpResponse(template.render({}, request))


def create(request):
    data = request.POST
    name = data['project-name']
    desc = data['project-desc']
    active_projects = Project.objects.filter(current_project=True)
    for pro in active_projects:
        pro.current_project = False
    project_model = Project(project_name=name, description=desc, current_project=True)
    project_model.save()
    return pinkproject(request)