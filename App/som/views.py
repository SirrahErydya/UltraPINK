from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template import loader
from django.db.models import QuerySet
from pinkproject.models import Project, Dataset
from som.models import SOM, Label, upload_to_som_folder
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
            'view': view,
            'half_som_width': int(active_som.som_width / 2)
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
    else:
        # Dataset
        dataset_name = data.get('dataset-name', None)
        dataset_descr = data.get('dataset-descr', None)
        cat_file = request.FILES.get('cat-data', None)
        data_file = request.FILES.get('dataset', None)
        dataset_model = dbe.create_dataset_models(dataset_name, dataset_descr, data_file, project_model, cat_file)

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

    dataset = get_data(dataset_model.data_path)
    if som_binfile and mapping_binfile:
        # pink_som = import_som(project_model, dataset_name, som_binfile, mapping_binfile, dataset, csv_file)
        raise NotImplementedError("Import of SOMs is currently not implemented")
    elif width and height and depth and layout and rotations and epochs:
        pink_som = train(dataset, (width, height, depth), layout, rotations, epochs)
    else:
        raise FileNotFoundError("No files to train or import are SOM are provided.")
    som_model = dbe.create_som_model(som_name, pink_som, (width, height, depth), dataset_model)

    # Save proto grid
    grid_path = upload_to_som_folder(som_model, "proto_grid.png")
    dbe.save_prototype_grid(som_model, grid_path)
    som_model.proto_grid.name = grid_path
    som_model.save()
    return redirect('pinkproject:project', project_id=project_id, som_id=som_model.id)


def map_prototypes(request, som_id):
    som_model = SOM.objects.get(id=som_id)
    save_path = upload_to_som_folder(som_model, "mapping.npy")
    mapping, heatmap = map_som(som_model)
    np.save(save_path, mapping)

    # Save heatmap
    heatmap_path = upload_to_som_folder(som_model, "heatmap.png")
    dbe.save_heatmap(heatmap, heatmap_path)

    # Save histrogram
    bmu_distances = np.min(mapping, axis=1)
    hist_path = upload_to_som_folder(som_model, "histogram.png")
    dbe.plot_histogram(bmu_distances, hist_path)

    # Update path links in model
    som_model.mapping_file = save_path
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
    distance_file = np.load(som_model.mapping_file)
    if len(protos) == 1:
        proto = get_protos_from_db(protos)[0]
        # Todo: Something is off here...
        # distances = get_distances(som_model, proto)
        # best_indices = np.argsort(distances)[:n_fits]
        data_points = DataPoint.objects.filter(som_id=som_model, closest_proto=proto)
        point_indices = [p.index for p in data_points]
        distances = distance_file[point_indices, proto.index]
    else:
        raise NotImplementedError("No multiple prototype selection for this time")
    json_points = []
    upper = n_fits if len(distances) > n_fits else len(distances)
    for i in range(upper):
        json_points.append(data_points[i].to_json(distances[i]))
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
    data_points = list(map(lambda idx: DataPoint.objects.get(som=som_model, index=idx), worst_indices))
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
