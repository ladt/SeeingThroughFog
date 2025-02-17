import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from tools.ProjectionTools.Lidar2RGB.lib.utils import project_pointcloud
from tools.ProjectionTools.Lidar2RGB.lib.utils import transform_coordinates
import numpy as np
from tools.CreateTFRecords.generic_tf_tools.resize import resize


def plot_spherical_scatter_plot(pointlcoud, pattern='hot', plot_show=True, title=None):
    norm = mpl.colors.Normalize(vmin=0, vmax=80)
    cmap = None
    if pattern == 'hot':
        cmap = cm.hot
    elif pattern == 'cool':
        cmap = cm.cool
    elif pattern == 'jet':
        cmap = cm.jet
    else:
        print('Wrong color map specified')
        exit()
    m = cm.ScalarMappable(norm, cmap)
    transformed_pointcloud = transform_coordinates(pointlcoud)
    depth_map_color = m.to_rgba(transformed_pointcloud[:, 0])

    plt.scatter(transformed_pointcloud[:, 1],
                transformed_pointcloud[:, 2], c=depth_map_color, s=1)

    if title is not None:
        plt.title(title)

    if plot_show:
        plt.show()


def plot_image_projection(pointcloud, vtc, velodyne_to_camera, frame='default', title=None):

    # Resize image to other crop
    r = resize(frame)

    lidar_image = project_pointcloud(pointcloud, np.matmul(r.get_image_scaling(), vtc), velodyne_to_camera,
                                     list(r.dsize)[::-1] + [3], init=np.zeros(list(r.dsize)[::-1] + [3]),
                                     draw_big_circle=True)

    if title is not None:
        plt.title(title)

    plt.imshow(lidar_image)
    plt.show()

# Aux function
def plot_lidar_projection_on_image(img_pth, pointcloud, vtc, velodyne_to_camera, frame='default', title=None, out_pth=None):
    # pointcloud.shape==(54837, 5)
    from PIL import Image

    # Resize image to other crop
    r = resize(frame)
    lidar_image, inter_lidar_image, inter_lidar_image_colormap = project_pointcloud(pointcloud, np.matmul(r.get_image_scaling(), vtc), velodyne_to_camera,
                                     list(r.dsize)[::-1] + [3], init=np.zeros(list(r.dsize)[::-1] + [3]),
                                     draw_big_circle=True)
    # lidar_image.shape==(1024, 1920, 3) - same as RGB image

    img = Image.open(img_pth)

    fig, ax = plt.subplots(2, 2)
    ax[0][1].imshow(img)
    ax[0][1].imshow(lidar_image, alpha=0.5)
    ax[0][1].title.set_text('raw Lidar on RGB image')
    ax[1][1].imshow(img)
    ax[1][1].imshow(inter_lidar_image_colormap, alpha=0.5)
    ax[1][1].title.set_text('interpolated Lidar on RGB image')
    ax[0][0].imshow(img)
    ax[0][0].title.set_text('raw RGB image')
    ax[1][0].imshow(inter_lidar_image)
    ax[1][0].title.set_text('interpolated Lidar (different depth colorspace)')
    plt.tight_layout()
    plt.show()

    # TODO
    # if title is not None:
    # plt.imshow(img)
    # plt.imshow(lidar_image, alpha=0.5)
    # plt.axis('off')
    # if not out_pth:
    #     plt.show()
    # else:
    #     plt.savefig(out_pth, bbox_inches='tight', dpi=300)


def plot_3d_scatter(pointlcoud, plot_show=True):
    fig = plt.figure()
    ax = plt.axes(projection="3d")

    ax.scatter3D(pointlcoud[:, 0], pointlcoud[:, 1], pointlcoud[:, 2], c='black', alpha=1, s=0.01)

    if plot_show:
        plt.show()
