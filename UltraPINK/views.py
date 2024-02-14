
from django.http import HttpResponse
from django.template import loader
from pinkproject.models import Project


def home(request):
    template = loader.get_template('main/home.html')
    context = {
        'projects': Project.objects.all()
    }
    return HttpResponse(template.render(context, request))


def all_projects(request):
    template = loader.get_template('main/all_projects.html')
    context = {
        'projects': Project.objects.all()
    }
    return HttpResponse(template.render(context, request))


def about(request):
    template = loader.get_template('main/about.html')
    return HttpResponse(template.render({}, request))
