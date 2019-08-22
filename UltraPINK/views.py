
from django.http import HttpResponse
from django.template import loader


def home(request):
    template = loader.get_template('main/home.html')
    context = {}
    return HttpResponse(template.render(context, request))
