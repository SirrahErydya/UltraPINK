from py4j.clientserver import ClientServer, JavaParameters
import sys


def make_gaia_dataset(cutouts, dataset):
    hook = {
        "name": "{0}-hook".format(dataset.dataset_name),
        "position": [0.0, 0.0, 0.0],

        "componentType": "Galaxies",

        "fadeIn": [1e3, 8e3],
        "fadeOut": [100e6, 200.0e6],

        "parent": "Universe",
        "archetype": "GenericCatalog",
        "cataloginfo": {
            "name": dataset.dataset_name,
            "description": dataset.description,
            "type": "INTERNAL",
            "nParticles": 100
        }
    }
    json_string = {
        "objects": [ hook ]
    }

    for cutout in cutouts:


def pass_to_gaiasky(dataset_name, dataset_path, fst_obj):
    gateway = ClientServer(java_parameters=JavaParameters(auto_convert=True))
    gs = gateway.entry_point
    #gs.backupSettings()
    gs.sleep(2) # Make sure that the data is available by adding this delay
    if gs.hasDataset(dataset_name):
        gs.removeDataset(dataset_name)
    gs.sleep(2)
    gs.loadDataset(dataset_name, dataset_path)
    gs.sleep(2)
    obj = gs.getObject(fst_obj)
    gs.setDatasetPointSizeMultiplier(dataset_name, 5.)

    gs.sleep(2)
    gs.goToObject(fst_obj, 1e-12)

    gateway.shutdown()


if __name__ == '__main__':
    ds_name = sys.argv[1]
    ds_path = sys.argv[2]
    fst_obj = sys.argv[3]

    pass_to_gaiasky(ds_name, ds_path, fst_obj)