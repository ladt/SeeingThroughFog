import matplotlib.pyplot as plt
import numpy as np
import cv2
import scipy.spatial
from sklearn.linear_model import RANSACRegressor
import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import lib.settings

def dense_map(Pts, n, m, grid):
    '''
    interpolate lidar depth
    :param Pts: num observations of (W, H, D) lidar coordinates (D - depth corrsponding to (W,H) image positions), Pts.shape==(3, num)
    :param n: image width
    :param m: image height
    :param grid: (grid*2+1) is neighborhood size
    :return:
    '''
    ng = 2 * grid + 1

    mX = np.zeros((m, n)) + np.float("inf")
    mY = np.zeros((m, n)) + np.float("inf")
    mD = np.zeros((m, n))
    mX[np.int32(Pts[1]), np.int32(Pts[0])] = Pts[0] - np.round(Pts[0])
    mY[np.int32(Pts[1]), np.int32(Pts[0])] = Pts[1] - np.round(Pts[1])
    mD[np.int32(Pts[1]), np.int32(Pts[0])] = Pts[2]

    KmX = np.zeros((ng, ng, m - ng, n - ng))
    KmY = np.zeros((ng, ng, m - ng, n - ng))
    KmD = np.zeros((ng, ng, m - ng, n - ng))

    for i in range(ng):
        for j in range(ng):
            KmX[i, j] = mX[i: (m - ng + i), j: (n - ng + j)] - grid - 1 + i
            KmY[i, j] = mY[i: (m - ng + i), j: (n - ng + j)] - grid - 1 + i
            KmD[i, j] = mD[i: (m - ng + i), j: (n - ng + j)]
    S = np.zeros_like(KmD[0, 0])
    Y = np.zeros_like(KmD[0, 0])

    for i in range(ng):
        for j in range(ng):
            s = 1 / np.sqrt(KmX[i, j] * KmX[i, j] + KmY[i, j] * KmY[i, j])
            Y = Y + s * KmD[i, j]
            S = S + s

    S[S == 0] = 1
    out = np.zeros((m, n))
    out[grid + 1: -grid, grid + 1: -grid] = Y / S
    return out


def project_pointcloud(lidar, vtc, velodyne_to_camera, image_shape, init=None, draw_big_circle=False):
    def py_func_project_3D_to_2D(points_3D, P):
        # Project on image
        points_2D = np.matmul(P, np.vstack((points_3D, np.ones([1, np.shape(points_3D)[1]]))))

        # scale projected points
        points_2D[0][:] = points_2D[0][:] / points_2D[2][:]
        points_2D[1][:] = points_2D[1][:] / points_2D[2][:]

        points_2D = points_2D[0:2]
        return points_2D.transpose()

    def py_func_create_lidar_img(lidar_points_2D, lidar_points, img_width=1248, img_height=375, init=None):
        # lidar_points_2d shape (19988, 2), each line is 2d image coordinates
        # lidar_points shape (3, 19988)
        within_image_boarder_width = np.logical_and(img_width > lidar_points_2D[:, 0], lidar_points_2D[:, 0] >= 0)
        within_image_boarder_height = np.logical_and(img_height > lidar_points_2D[:, 1], lidar_points_2D[:, 1] >= 0)

        valid_points = np.logical_and(within_image_boarder_width, within_image_boarder_height) #(19988,) boolean array
        coordinates = np.where(valid_points)[0] #(4222,) - enteries of valid points in lidar_points
        values = lidar_points[:, coordinates] #(3, 4222)

        if init is None:
            image = -120.0 * np.ones((img_width, img_height, 3)) #image.shape==(1920, 1024, 3)
        else:
            image = init.transpose((1, 0, 2))  #image.shape==(1920, 1024, 3), zeroes

        img_coordinates = lidar_points_2D[coordinates, :].astype(dtype=np.int32) #(4222, 2)

        final_coordinates = np.concatenate((img_coordinates, values.transpose()[:, 1][:, np.newaxis]), 1).transpose()
        inter_image = dense_map(final_coordinates, img_width, img_height, grid=lib.settings.grid_size)

        import matplotlib as mpl
        import matplotlib.cm as cm

        norm = mpl.colors.Normalize(vmin=0, vmax=80)
        cmap = cm.jet
        m = cm.ScalarMappable(norm, cmap)

        depth_map_color = np.copy(inter_image).reshape(-1)
        depth_map_color = m.to_rgba(depth_map_color)
        depth_map_color = (255 * depth_map_color).astype(dtype=np.uint8)
        depth_map_color = np.array(depth_map_color)[:, :3]
        depth_map_color = depth_map_color.reshape((inter_image.shape[0], inter_image.shape[1], 3))
        inter_image_colormap = depth_map_color


        if not draw_big_circle:
            image[img_coordinates[:, 0], img_coordinates[:, 1], :] = values.transpose() # image is (1920, 1024, 3), values.transpose() is (4222, 3)
        else:
            # Slow elementwise circle drawing through opencv
            len = img_coordinates.shape[0]
            image = image.transpose([1, 0, 2]).squeeze().copy()

            depth_map_color = values.transpose()[:, 1] #values.transpose is (4222, 3), [:, 1] is depth (z)
            depth_map_color = m.to_rgba(depth_map_color)
            depth_map_color = (255 * depth_map_color).astype(dtype=np.uint8)


            for idx in range(len):
                x, y = img_coordinates[idx, :]
                value = depth_map_color[idx]
                # print value
                tupel_value = (int(value[0]), int(value[1]), int(value[2]))
                # print tupel_value
                cv2.circle(image, (x, y), 1, tupel_value, -1) # TODO was 3
            return image, inter_image, inter_image_colormap #(1024, 1920, 3)

        return image.transpose([1, 0, 2]).squeeze() #(1024, 1920, 3)

    def py_func_lidar_projection(lidar_points_3D, vtc, velodyne_to_camera, shape, init=None):  # input):

        img_width = shape[1]
        img_height = shape[0]
        # print img_height, img_width
        lidar_points_3D = lidar_points_3D[:, 0:4] #(54837, 4)

        # Filer away all points behind image plane
        min_x = 2.5
        valid = lidar_points_3D[:, 0] > min_x
        # extend projection matrix to 5d to efficiently parse intensity
        lidar_points_3D = lidar_points_3D[np.where(valid)]
        lidar_points_3D2 = np.ones((lidar_points_3D.shape[0], lidar_points_3D.shape[1] + 1))
        lidar_points_3D2[:, 0:3] = lidar_points_3D[:, 0:3]
        lidar_points_3D2[:, 4] = lidar_points_3D[:, 3]
        # Extend projection matric to pass trough intensities
        velodyne_to_camera2 = np.zeros((5, 5))
        velodyne_to_camera2[0:4, 0:4] = velodyne_to_camera
        velodyne_to_camera2[4, 4] = 1

        lidar_points_2D = py_func_project_3D_to_2D(lidar_points_3D.transpose()[:][0:3], vtc) #lidar_points_2d.shape=(19988, 2)
        pts_3D = np.matmul(velodyne_to_camera2, lidar_points_3D2.transpose())
        # detelete placeholder 1 axis
        pts_3D = np.delete(pts_3D, 3, axis=0) #pts_3d.shape==(4, 19988)

        pts_3D_yzi = pts_3D[1:, :] #(3, 19988)

        return py_func_create_lidar_img(lidar_points_2D, pts_3D_yzi, img_width=img_width,
                                        img_height=img_height, init=init)
    # lidar.shape==(54837, 5)
    return py_func_lidar_projection(lidar, vtc, velodyne_to_camera, image_shape, init=init)


def find_missing_points(last, strongest):
    last_set = set([tuple(x) for x in last])
    strong_set = set([tuple(x) for x in strongest])
    remaining_last = np.array([x for x in last_set - strong_set])
    remaining_strong = np.array([x for x in strong_set - last_set])

    return remaining_last, remaining_strong


def transform_coordinates(xyz):
    """
    Takes as input a Pointcloud with xyz coordinates and appends spherical coordinates as columns
    :param xyz:
    :return: Pointcloud with following columns, r, phi, theta, ring, intensity, x, y, z, intensity, ring
    """

    ptsnew = np.hstack((np.zeros_like(xyz), xyz))
    r_phi = xyz[:, 0] ** 2 + xyz[:, 1] ** 2
    ptsnew[:, 0] = np.sqrt(r_phi + xyz[:, 2] ** 2)
    ptsnew[:, 2] = np.pi / 2 - np.arctan2(np.sqrt(r_phi), xyz[:, 2])  # for elevation angle defined from Z-axis down

    ptsnew[:, 1] = np.arctan2(xyz[:, 1], xyz[:, 0])
    ptsnew[:, 3] = xyz[:, 4]
    ptsnew[:, 4] = xyz[:, 3]

    return ptsnew


def find_closest_neighbors(x, reference):
    """
    This function allows you to match strongest and last echos and reason about scattering distributions.

    :param x: Pointcloud which should be matched
    :param reference: Reference Pointcloud
    :return: returns valid matching indexes
    """
    tree = scipy.spatial.KDTree(reference[:, 1:4])
    distances, indexes = tree.query(x[:, 1:4], p=2)
    print('indexes', indexes)
    print('found matches', len(indexes), len(set(indexes)))
    # return 0
    valid = []
    # not matching contains all not explainable scattered mismatching particles
    not_matching = []
    for idx, i in enumerate(indexes):

        delta = reference[i, :] - x[idx, :]
        # Laser Ring has to match
        if delta[-1] == 0:

            # Follows assumption that strongest echo has higher intensity than last and that the range is more distant
            # for the last return. The sensor can report 2 strongest echo if strongest and last echo are matching.
            # Here those points are not being matched.
            if delta[-2] < 0 and delta[0] > 0:
                valid.append((i, idx))
            else:
                not_matching.append((i, idx))
        else:
            not_matching.append((i, idx))

    return valid


def filter(lidar_data, distance):
    """
    Takes lidar Pointcloud as ibnput and filters point below distance threshold
    :param lidar_data: Input Pointcloud
    :param distance: Minimum distance for filtering
    :return: Filtered Pointcloud
    """

    r = np.sqrt(lidar_data[:, 0] ** 2 + lidar_data[:, 1] ** 2 + lidar_data[:, 2] ** 2)
    true_idx = np.where(r > distance)

    lidar_data = lidar_data[true_idx, :]

    return lidar_data[0]


def read_split(split):
    with open(split, 'r') as f:
        entry_ids = f.readlines()

    entry_ids = [i.replace('\n', '') for i in entry_ids]
    return entry_ids


def filter_below_groundplane(pointcloud, tolerance=1):
    valid_loc = (pointcloud[:, 2] < -1.4) & \
                (pointcloud[:, 2] > -1.86) & \
                (pointcloud[:, 0] > 0) & \
                (pointcloud[:, 0] < 40) & \
                (pointcloud[:, 1] > -15) & \
                (pointcloud[:, 1] < 15)
    pc_rect = pointcloud[valid_loc]
    print(pc_rect.shape)
    if pc_rect.shape[0] <= pc_rect.shape[1]:
        w = [0, 0, 1]
        h = -1.55
    else:
        reg = RANSACRegressor().fit(pc_rect[:, [0, 1]], pc_rect[:, 2])
        w = np.zeros(3)
        w[0] = reg.estimator_.coef_[0]
        w[1] = reg.estimator_.coef_[1]
        w[2] = 1.0
        h = reg.estimator_.intercept_
        w = w / np.linalg.norm(w)

        print(reg.estimator_.coef_)
        print(reg.get_params())
        print(w, h)
    height_over_ground = np.matmul(pointcloud[:, :3], np.asarray(w))
    height_over_ground = height_over_ground.reshape((len(height_over_ground), 1))
    above_ground = np.matmul(pointcloud[:, :3], np.asarray(w)) - h > -tolerance
    print(above_ground.shape)
    return np.hstack((pointcloud[above_ground, :], height_over_ground[above_ground]))
