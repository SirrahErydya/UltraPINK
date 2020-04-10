from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template import loader
from django.db.models import QuerySet
from pinkproject.models import Project, Dataset
from som.models import SOM
from som.som import *
import UltraPINK.create_database_entries as dbe
import json
import sys, traceback


# Create your views here.
def som(request, project):
    template = loader.get_template("som/som.html")
    soms = QuerySet(SOM)
    datasets = Dataset.objects.filter(project=project)
    for ds in datasets:
        soms = soms | SOM.objects.filter(dataset=ds)
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
    soms = QuerySet(SOM)
    datasets = Dataset.objects.filter(project=project_model)
    for ds in datasets:
        soms = soms | SOM.objects.filter(dataset=ds)
    template = loader.get_template("som/add_som.html")
    context = {
        # Pass some values from the backend here
        'current': project_model,
        'soms': soms
    }
    return HttpResponse(template.render(context, request))


def save_som(request, project_id):
    project_model = Project.objects.get(id=project_id)

    # Dataset
    data = request.POST
    dataset_name = data.get('dataset-name', None)
    csv_file = request.FILES.get('csv-data', None)
    data_path = request.FILES.get('dataset', None)
    dataset = get_data(data_path)
    dataset_model = dbe.create_dataset_models(dataset_name, dataset, project_model, csv_file)

    # Input for SOM training
    som_name = data.get('som_name', None)
    width = data.get('som_width', None)
    height = data.get('som_height', None)
    depth = data.get('som_depth', None)
    layout = data.get('layout', None)
    rotations = data.get('rotations', None)
    epochs = data.get('epochs', None)

    # Input for SOM import
    som_binfile = request.FILES.get('som-file', None)
    mapping_binfile = request.FILES.get('mapping-file', None)

    if som_binfile and mapping_binfile:
        pink_som = import_som(project_model, dataset_name, som_binfile, mapping_binfile, dataset, csv_file)
    elif width and height and depth and layout and rotations and epochs:
        pink_som = train(dataset, (width, height, depth), layout, rotations, epochs)
    else:
        raise FileNotFoundError("No files to train or import are SOM are provided.")
    som_model = dbe.create_som_model(som_name, pink_som, dataset_model)
    return redirect('pinkproject:project', project_id=project_id, som_id=som_model.id)


def get_protos(request):
    protos = get_protos(json.loads(request.body)['protos'])
    json_protos = [prototype.to_json() for prototype in protos]
    return JsonResponse({'protos': json_protos, "success": True})


def get_best_fits_to_protos(request, n_fits=10):
    protos = json.loads(request.body)['protos']
    if len(protos) == 1:
        cutouts = get_best_fits(protos[0], n_fits)
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
            label_protos(protos, label)
            return JsonResponse({"success": True})
        if cutouts:
            label_cutouts(cutouts, label)
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
            entries = [DataPoint.objects.get(id=cutout_id) for cutout_id in data['cutout_ids']]
        elif 'outlier_ids' in data.keys():
            entries = [Outlier.objects.get(id=outlier_id) for outlier_id in data['outlier_ids']]
        else:
            entries = DataPoint.objects.all()
        export_catalog(entries, filename)
        return JsonResponse({'success': True})
    except:
        traceback.print_exc(file=sys.stdout)
        return JsonResponse({"success": False})
