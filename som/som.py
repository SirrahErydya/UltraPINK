"""
Create, train and import SOMs with PINK
:author: Fenja Kollasch
"""
import pink
import numpy as np
import math


def train(raw_data, som_dim, epochs):
    """
    Create (and train) a new SOM for a given data set
    :param raw_data: The training data as a .npy file
    :param som_dim: Dimensions of the resulting SOM
    :param epochs: Training epochs
    :return: A trained SOM object
    """
    np.random.shuffle(raw_data)
    raw_data = np.squeeze(raw_data)
    neuron_dim = int(raw_data.shape[1] / math.sqrt(2.0) * 2.0)
    euclid_dim = int(raw_data.shape[1] * math.sqrt(2.0) / 2.0)
    np_som = np.zeros((som_dim, som_dim, neuron_dim, neuron_dim)).astype(np.float32)
    som = pink.SOM(np_som)

    pink_data = [pink.Data(raw_data[i]) for i in range(len(raw_data))]
    trainer = pink.Trainer(som, euclidean_distance_dim=euclid_dim, distribution_function=pink.GaussianFunctor(1.1, 0.2))

    for _ in epochs:
        for point in pink_data:
            trainer(point)
    trainer.update_som()
    return som
