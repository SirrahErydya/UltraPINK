from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template import loader
from pinkproject.models import Project
from som.models import Prototype, SOM, Outlier, SomCutout
from pinkproject.views import create_som, pinkproject
#import som.som_analysis as sa
import som.create_database_entries as dbe
import json
import sys, traceback


# Create your views here.
def som(request, project):
    template = loader.get_template("som/som.html")
    soms = SOM.objects.filter(project=project)
    active_som = soms.get(current=True)
    prototypes = Prototype.objects.filter(som=active_som).order_by('y', 'x')
    context = {
        # Pass some values from the backend here
        'prototypes': prototypes,
        'all_soms': soms,
        'active_som': active_som
    }
    return HttpResponse(template.render(context, request))


def add_som(request, project_id=1):
    project_model = Project.objects.get(id=project_id)
    soms = SOM.objects.filter(project=project_model)
    template = loader.get_template("som/add_som.html")
    context = {
        # Pass some values from the backend here
        'current': project_model,
        'soms': soms
    }
    return HttpResponse(template.render(context, request))


def save_som(request, project_id):
    data = request.POST
    # File handling
    dataset_name = data.get('dataset-name', None)
    csv_file = request.FILES.get('csv-data', None)
    som_binfile = request.FILES.get('som-file', None)
    mapping_binfile = request.FILES.get('mapping-file', None)
    data_binfile = request.FILES.get('image-file', None)

    project_model = Project.objects.get(id=project_id)
    project_model.save()
    som_id = create_som(project_model, dataset_name, som_binfile, mapping_binfile,
               data_binfile, csv_file)
    return redirect('pinkproject:project', project_id=project_id, som_id=som_id)


def get_protos(request):
    protos = sa.get_protos(json.loads(request.body)['protos'])
    json_protos = [prototype.to_json() for prototype in protos]
    return JsonResponse({'protos': json_protos, "success": True})


def get_best_fits_to_protos(request, n_fits=10):
    protos = json.loads(request.body)['protos']
    if len(protos) == 1:
        cutouts = sa.get_best_fits(protos[0], n_fits)
    else:
        raise NotImplementedError("No multiple prototype selection for this time")
    json_cutouts = [cutout.to_json() for cutout in cutouts]
    return JsonResponse({'best_fits': json_cutouts, "success": True})


def label(request, label):
    data = json.loads(request.body)
    protos, cutouts = None, None
    if 'protos' in data.keys():
        protos = data['protos']
    if 'cutouts' in data.keys():
        cutouts = data['cutouts']
    try:
        if protos:
            sa.label_protos(protos, label)
            return JsonResponse({"success": True})
        if cutouts:
            sa.label_cutouts(cutouts, label)
            return JsonResponse({"success": True})
        return JsonResponse({"success": False})
    except:
        traceback.print_exc(file=sys.stdout)
        return JsonResponse({"success": False})


def get_outliers(request, som_id, n_fits=10):
    outliers = Outlier.objects.all()[:n_fits]
    if len(outliers) < n_fits:
        outliers = dbe.create_outliers(som_id, n_fits)
    json_outliers = [outlier.to_json() for outlier in outliers]
    return JsonResponse({'best_fits':  json_outliers, 'success': True})


def export_catalog(request, filename):
    data = json.loads(request.body)
    try:
        if 'cutout_ids' in data.keys():
            entries = [SomCutout.objects.get(id=cutout_id) for cutout_id in data['cutout_ids']]
        elif 'outlier_ids' in data.keys():
            entries = [Outlier.objects.get(id=outlier_id) for outlier_id in data['outlier_ids']]
        else:
            entries = SomCutout.objects.all()
        sa.export_catalog(entries, filename)
        return JsonResponse({'success': True})
    except:
        traceback.print_exc(file=sys.stdout)
        return JsonResponse({"success": False})
