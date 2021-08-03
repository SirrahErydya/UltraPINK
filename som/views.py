from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template import loader
from django.db.models import QuerySet
from pinkproject.models import Project, Dataset
from som.models import SOM, Label
from som.som import *
import UltraPINK.create_database_entries as dbe
import json
import sys, traceback


def som(request, som_id, view='proto'):
    template = loader.get_template("pinkproject/project.html")
    active_som = SOM.objects.get(id=som_id)
    if active_som:
        print("Som will be rendered")
        prototypes = Prototype.objects.filter(som=active_som)
        labels = Label.objects.filter(som=active_som)
        context = {
            # Pass some values from the backend here
            'current': active_som.dataset.project,
            'active_som': active_som,
            'prototypes': prototypes,
            'labels': labels,
            'view': view
        }
        return HttpResponse(template.render(context, request))
    raise FileNotFoundError("SOM not found.")


def add_som(request, project_id=1, dataset_id=None):
    project_model = Project.objects.get(id=project_id)
    if dataset_id:
        current_ds = Dataset.objects.get(id=dataset_id)
    else:
        current_ds = None
    soms = QuerySet(SOM)
    datasets = Dataset.objects.filter(project=project_model)
    for ds in datasets:
        soms = soms | SOM.objects.filter(dataset=ds)
    template = loader.get_template("som/add_som.html")
    context = {
        # Pass some values from the backend here
        'current': project_model,
        'soms': soms,
        'dataset': current_ds,
        'datasets': datasets
    }
    return HttpResponse(template.render(context, request))


def save_som(request, project_id, dataset_id=None):
    data = request.POST
    project_model = Project.objects.get(id=project_id)
    if dataset_id:
        dataset_model = Dataset.objects.get(id=dataset_id)
        dataset = get_data(dataset_model.data_path)
    else:
        # Dataset
        dataset_name = data.get('dataset-name', None)
        dataset_descr = data.get('dataset-descr', None)
        csv_file = request.FILES.get('csv-data', None)
        data_path = request.FILES.get('dataset', None)
        dataset = get_data(data_path)
        dataset_model = dbe.create_dataset_models(dataset_name, dataset_descr, dataset, project_model, csv_file)

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
        # pink_som = import_som(project_model, dataset_name, som_binfile, mapping_binfile, dataset, csv_file)
        raise NotImplementedError("Import of SOMS is currently not implemented")
    elif width and height and depth and layout and rotations and epochs:
        pink_som = train(dataset, (width, height, depth), layout, rotations, epochs)
    else:
        raise FileNotFoundError("No files to train or import are SOM are provided.")
    som_model = dbe.create_som_model(som_name, pink_som, dataset_model)
    return redirect('pinkproject:project', project_id=project_id, som_id=som_model.id)


def map_prototypes(request, som_id):
    som_model = SOM.objects.get(id=som_id)
    save_path = os.path.join('projects', som_model.dataset.project.project_name, "soms", som_model.som_name)
    mapping, heatmap = map_som(som_model)
    np.save(os.path.join(save_path, "mapping.npy"), mapping)
    heatmap_path = os.path.join(save_path, "heatmap.png")
    dbe.save_heatmap(heatmap, heatmap_path)
    bmu_distances = np.min(mapping, axis=1)
    hist_path = os.path.join(save_path, 'histogram.png')
    dbe.plot_histogram(bmu_distances, hist_path)
    som_model.mapping_file = os.path.join(save_path, "mapping.npy")
    som_model.heatmap.name = heatmap_path
    som_model.histogram.name = hist_path
    som_model.mapping_generated = True
    som_model.save()
    return redirect('pinkproject:project', project_id=som_model.dataset.project.id, som_id=som_id)


def get_protos(request):
    protos = get_protos_from_db(json.loads(request.body)['protos'])
    json_protos = [prototype.to_json() for prototype in protos]
    print(json_protos)
    return JsonResponse({'protos': json_protos, "success": True})


def get_best_fits_to_protos(request, som_id, n_fits=10):
    som_model = SOM.objects.get(id=som_id)
    protos = json.loads(request.body)['protos']
    if len(protos) == 1:
        proto = get_protos_from_db(protos)[0]
        distances = get_distances(som_model, proto)
        best_indices = np.argsort(distances)[:n_fits]
        data_points = list(map(lambda idx: DataPoint.objects.get(dataset=som_model.dataset, index=idx), best_indices))
    else:
        raise NotImplementedError("No multiple prototype selection for this time")
    json_points = []
    upper = n_fits if len(distances) > n_fits else len(distances)
    for i in range(upper):
        json_points.append(data_points[i].to_json(distances[best_indices[i]]))
    return JsonResponse({'best_fits': json_points, "success": True})


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
    som_model = SOM.objects.get(id=som_id)
    distances = get_distances(som_model)
    worst_distances = np.max(distances, axis=1)
    worst_indices = np.argsort(-worst_distances)[:n_fits]
    data_points = list(map(lambda idx: DataPoint.objects.get(dataset=som_model.dataset, index=idx), worst_indices))
    json_outliers = [outlier.to_json() for outlier in data_points]
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
