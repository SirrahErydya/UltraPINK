
from django.http import HttpResponse
from django.template import loader
from pinkproject.models import Project


def home(request):
    template = loader.get_template('main/home.html')
    context = {
        'projects': Project.objects.all()
    }
    return HttpResponse(template.render(context, request))
