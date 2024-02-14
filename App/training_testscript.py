import pink
import numpy as np
import math
import os
from tqdm import tqdm
from PIL import Image, ImageDraw
from matplotlib import pyplot as plt
from matplotlib import gridspec as gridspec
from matplotlib import image as mpimg

if __name__ == "__main__":

    layout = 'hexagonal-2d'
    som_dim = (5,5,1)
    number_of_rotations = 360
    epochs = 1

    data_path = os.path.join('/home/kollasfa/UltraPINK', 'projects', 'MyFirstHexProject', 'datasets', 'GalaxyZoo', "GalaxyZoo.npy")
    data = np.load(data_path)
    np.random.shuffle(data)
    data = np.squeeze(data)
    neuron_dim = int(data.shape[1] / math.sqrt(2.0) * 2.0)



    def train():
        """
        Create (and train) a new SOM for a given data set
        :param data: The path to the raw data
        :param som_dim: Dimensions of the resulting SOM
        :param layout: The SOM layout (hexagonal or cartesian)
        :param number_of_rotations: Number of rotations
        :param epochs: Training epochs
        :return: A trained SOM object
        """

        euclid_dim = int(data.shape[1] * math.sqrt(2.0) / 2.0)
        width, height, depth = som_dim
        if layout == 'cartesian-2d':
            np_som = np.zeros((int(width), int(height), neuron_dim, neuron_dim)).astype(np.float32)
        elif layout == 'hexagonal-2d':
            #@ Todo: Only for square-shaped 2D hex soms
            radius = (int(width) - 1) / 2
            number_of_neurons = int(int(width) * int(height) - radius * (radius + 1))
            np_som = np.random.rand(number_of_neurons, neuron_dim, neuron_dim).astype(np.float32)
        else:
            raise AttributeError("Invalid layout: {0}".format(layout))
        som = pink.SOM(np_som, som_layout=layout)

        trainer = pink.Trainer(som, number_of_rotations=int(number_of_rotations), euclidean_distance_dim=euclid_dim,
                               distribution_function=pink.GaussianFunctor(1.1, 0.2))
        print("Start training...")
        for e in range(int(epochs)):
            print("Epoch {0}".format(e+1))
            for point in tqdm(data):
                point = point.astype(np.float32)
                if point.max() > 1:
                    point = point/255
                trainer(pink.Data(point))
        trainer.update_som()
        return som


    #my_som = train()
    #np_som = np.array(my_som)
    #np.save("/home/kollasfa/UltraPINK/test_som.npy", np_som)
    np_som = np.load("/home/kollasfa/UltraPINK/test_som.npy")

    figure = plt.figure(figsize=(10, 10), frameon=False)
    grid = gridspec.GridSpec(som_dim[0], som_dim[0], wspace=0.0, hspace=0.0,
                             bottom=0, top=1, left=0, right=1)
    fig, ax = plt.subplots(1, figsize=(10, 10))

    som_width = som_dim[0] # assume squared som
    border = 1
    image = Image.new('RGB', (int(som_width*neuron_dim + (som_width-1)*border),
                              int(neuron_dim + (som_width-1)*(0.77*neuron_dim) + (som_width-2)* border)),
                              (255, 255, 255))
    x_pos = 0
    y_pos = 0
    som_idx = 0
    for row in range(som_width):
        cols_allowed = int(som_width - (np.abs(row - np.floor(som_width/2))))
        x_pos = int(((som_dim[0] - cols_allowed) / 2)*neuron_dim)
        y_pos = int(row * (0.77*neuron_dim))
        if row != 0 and row != som_width-1:
            y_pos += border
        print("X:", x_pos)
        print("Y:", y_pos)
        for col in range(cols_allowed):
            pil_image = Image.fromarray(np_som[som_idx] * 255)
            pil_image = pil_image.convert('L')
            mask = Image.new('RGBA', pil_image.size)
            d = ImageDraw.Draw(mask)
            d.polygon(((neuron_dim / 2, 0), (neuron_dim, neuron_dim / 4), (neuron_dim, 3 * neuron_dim / 4),
                       (neuron_dim / 2, neuron_dim), (0, 3 * neuron_dim / 4), (0, neuron_dim / 4)), fill='#FFF')
            image.paste(pil_image, (x_pos, y_pos), mask)
            x_pos += neuron_dim
            if col != cols_allowed-1:
                x_pos += border
            som_idx += 1

    image.show()

