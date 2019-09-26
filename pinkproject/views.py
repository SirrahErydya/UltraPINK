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


def pinkproject(request, project_id, som_id=None):
    template = loader.get_template("pinkproject/project.html")
    no_template = loader.get_template("pinkproject/no_project.html")
    try:
        current_project = Project.objects.get(id=project_id)
        soms = SOM.objects.filter(project=current_project)
        if som_id is not None:
            active_som = SOM.objects.get(id=som_id)
            assert active_som.project_id == project_id
        elif len(soms) > 0:
            active_som = soms[0]
        else:
            active_som = None
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
    create_som(project_model, dataset_name, som_binfile, mapping_binfile,
               data_binfile, None, csv_file)
    return pinkproject(request)


def create_som(project, dataset_name, som_binfile, mapping_binfile,
               data_binfile=None, csv_file=None):
    bin_dir = os.path.join(settings.BIN_DIR, dataset_name)
    data_dir = os.path.join(settings.DATA_DIR, dataset_name)
    fs = FileSystemStorage()
    if data_binfile is not None:
        data_file_name = fs.save(os.path.join(bin_dir, data_binfile.name), data_binfile)
    else:
        raise FileNotFoundError('You need a binary file containing the images.')
    som_file_name = fs.save(os.path.join(bin_dir, som_binfile.name), som_binfile)
    mapping_file_name = fs.save(os.path.join(bin_dir, mapping_binfile.name), mapping_binfile)
    csv_file_name = fs.save(os.path.join(data_dir, csv_file.name), csv_file)
    som_obj_path = os.path.join(settings.BIN_DIR, dataset_name, 'som_' + dataset_name + '.pkl')

    som_obj = SOM_obj(dataset_name, som_file_name, mapping_file_name, som_obj_path)
    som_obj.save()

    # Creating directories
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'prototypes', som_obj.training_dataset_name), exist_ok=True)
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'outliers', som_obj.training_dataset_name), exist_ok=True)

    som_model = db.create_som_model(project, som_file_name, mapping_file_name, data_file_name, csv_file_name, som_obj)

    # Create prototype entries and save the plots
    db.create_prototype_models(som_model, som_obj.data_som)

    return som_model.id
