from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.core.exceptions import ObjectDoesNotExist
from pinkproject.models import Project
from som.models import SOM, Prototype
from django.conf import settings
import os
from django.core.files.storage import FileSystemStorage
import som.create_database_entries as db
from som.som_postprocessing import SOM as SOM_obj
import csv


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
        active_som = soms.get(current=True)
        prototypes = Prototype.objects.filter(som=active_som).order_by('y', 'x')
        context = {
            # Pass some values from the backend here
            'current': current_project,
            'soms': soms,
            'active_som': active_som,
            'prototypes': prototypes
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
    # File handling
    dataset_name = data.get('dataset-name', None)
    n_cutouts = data['n_cutouts']
    n_outliers = data['n_outliers']
    #data_file = data.get('img-data', None)
    csv_file = request.FILES.get('csv-data', None)
    som_binfile = request.FILES.get('som-file', None)
    mapping_binfile = request.FILES.get('mapping-file', None)
    data_binfile = request.FILES.get('image-file', None)

    if project_id is None:
        project_model = Project(project_name=name, description=desc)
    else:
        project_model = Project.objects.get(id=project_id)
        project_model.project_name = name
        project_model.description = desc
    project_model.save()
    load_project(project_model)
    create_som(project_model, dataset_name, som_binfile, mapping_binfile, int(n_cutouts), int(n_outliers),
               data_binfile, None, csv_file)
    return pinkproject(request)


def create_som(project, dataset_name, som_binfile, mapping_binfile, n_cutouts, n_outliers,
               data_binfile=None, data_file=None, csv_file=None):
    bin_dir = os.path.join(settings.BIN_DIR, dataset_name)
    data_dir = os.path.join(settings.DATA_DIR, dataset_name)
    fs = FileSystemStorage()
    if data_binfile is not None:
        data_file_name = fs.save(os.path.join(bin_dir, data_binfile.name), data_binfile)
    elif data_file is not None:
        raise NotImplementedError('Image folders are not supported yet.')
    else:
        raise FileNotFoundError('You either need a binary file containing the images or a link to the image folder')
    som_file_name = fs.save(os.path.join(bin_dir, som_binfile.name), som_binfile)
    mapping_file_name = fs.save(os.path.join(bin_dir, mapping_binfile.name), mapping_binfile)
    csv_file_name = fs.save(os.path.join(data_dir, csv_file.name), csv_file)

    som_obj = SOM_obj(dataset_name, som_file_name, mapping_file_name)

    # Creating directories
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'prototypes', som_obj.training_dataset_name), exist_ok=True)
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'cutouts', som_obj.training_dataset_name), exist_ok=True)
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'outliers', som_obj.training_dataset_name), exist_ok=True)

    som_model = db.create_som_model(project, som_file_name, mapping_file_name, data_file_name, csv_file_name, som_obj,
                                    n_cutouts=n_cutouts, n_outliers=n_outliers)

    # Create prototype entries and save the plots
    db.create_prototype_models(som_model, som_obj.data_som)

    # Create cutouts and distances
    with open(som_model.csv_path.path) as csv_file:
        catalog = csv.DictReader(csv_file)
        db.create_cutout_models(som_model, som_obj.data_map, catalog, som_model.n_cutouts)

        # Create outliers
        db.create_outliers(som_model, som_obj.data_map, catalog, som_model.n_outliers)




def load_project(project):
    active_projects = Project.objects.filter(current_project=True)
    for pro in active_projects:
        pro.current_project = False
        pro.save()
    project.current_project = True
    project.save()

