from django.test import TestCase
import matplotlib.pyplot as plt
import numpy as np


# Create your tests here.
def test_heatmap():
    heatmap = np.array(
        [[1, 7, 1],
         [4, 9, 4],
         [1, 7, 1]]
    )
    figure = plt.figure(figsize=heatmap.shape, frameon=False)
    axis = plt.Axes(figure, [0., 0., 1., 1.])
    axis.set_axis_off()
    figure.add_axes(axis)
    for y in range(heatmap.shape[0]):
        for x in range(heatmap.shape[1]):
            axis.text(x, y, heatmap[y][x], ha="center", va="center", color="w")
    axis.imshow(heatmap)
    figure.savefig('heatmap.png')
    plt.close()


def test_hist():
    mapping = np.load('/home/kollasfa/UltraPINK/projects/SuperAwesomeProject/soms/GalaxyZoo4x4/mapping.npy')
    dists = np.min(mapping, axis=1)
    print(dists)
    plt.hist(dists, bins=100)
    plt.xlabel('Summed Euclidian (SE) distance to best matching prototype')
    plt.ylabel('Number of sources per bin')
    plt.tight_layout()
    plt.savefig('histogram.png', transparent=True)
    plt.close()


if __name__ == '__main__':
    test_heatmap()
    test_hist()