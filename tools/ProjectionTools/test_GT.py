# test_GT

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
# import scipy.interpolate as sciint
# import cv2
import os
import shutil

def gt_to_2dbox(in_dir, out_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    for file_path in in_dir:
        file_name = Path(file_path.split('.')[0]).stem
        new_file_path = os.path.join(out_dir, file_name)
        with open(file_path, 'r') as in_file:
            with open(new_file_path, 'w') as out_file:
                for line in in_file:
                    box = line.split(' ')[4: 8]
                    line_box = ' '.join(box)
                    out_file.write(line_box)

def compare_files(dir1, dir2):
    for file_path1 in dir1:
        file_name = Path(file_path1.split('.')[0]).stem
        file_path2 = os.path.join(dir2, file_name)
        with open(file_path1, 'r') as file1:
            with open(file_path2, 'r') as file2:
                if set(file1) != set(file2):
                    print(file_name)

if __name__ == '__main__':
    indir1 =
    indir2 =
    out_dir1 =
    out_dir2 =
    gt_to_2dbox(in_dir1, bbox_2d_dir1)
    gt_to_2dbox(in_dir2, bbox_2d_dir2)
    compare_files(bbox_2d_dir1, bbox_2d_dir2)


# Naama's

# str = '2018-02-05_12-10-27_00200'
# vis_im = cv2.imread('vis_' + str + '.png')
# gated_proj_elad_im = cv2.imread('gated0_elad_' + str + '_adjust.png')
# gt_text = np.loadtxt('labels_' + str + '_Naama.txt')
# x_offset = 290
# y_offset = 205
#
# print(gt_text)
#
# num_labels = gt_text.shape[0]
# for l in range(num_labels):
#     topleft = (int(gt_text[l,0]), int(gt_text[l,1]))
#     botright = (int(gt_text[l,2]), int(gt_text[l,3]))
#     cv2.rectangle(vis_im, topleft, botright, (255, 0, 0), 2)
#
#     topleft_offset = (int(gt_text[l,0]-x_offset), int(gt_text[l,1]-y_offset))
#     botright_offset = (int(gt_text[l,2]-x_offset), int(gt_text[l,3]-y_offset))
#     cv2.rectangle(gated_proj_elad_im, topleft_offset, botright_offset, (255, 0, 0), 2)
#
#
# cv2.imwrite('vis_gt.png', vis_im)
# cv2.imwrite('gated_proj_elad_gt.png', gated_proj_elad_im)