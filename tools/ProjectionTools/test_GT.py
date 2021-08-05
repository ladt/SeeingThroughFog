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
    for file_name in os.listdir(in_dir):
        if not file_name.endswith('.txt'): continue
        file_path = os.path.join(in_dir, file_name)
        new_file_path = os.path.join(out_dir, file_name)
        with open(file_path, 'r') as in_file:
            with open(new_file_path, 'w') as out_file:
                for line in in_file:
                    box = line.split(' ')[4: 8]
                    line_box = ' '.join(box)
                    out_file.write(line_box + '\n')

def compare_files(dir1, dir2):
    total_count = 0
    diff_count = 0
    same_non_empty_count = 0
    with open('diff.txt', 'w') as diff_file:
        for file_name1 in os.listdir(dir1):
            file_path1 = os.path.join(dir1, file_name1)
            file_path2 = os.path.join(dir2, file_name1)
            with open(file_path1, 'r') as file1:
                with open(file_path2, 'r') as file2:
                    lines1, lines2 = set(file1), set(file2)
                    total_count += 1
                    num_lines1, num_lines2 = len(lines1), len(lines2)
                    if lines1 != lines2: # compare lines, order doesn't matter
                        diff_count += 1
                        lines_num_diff = ''
                        if num_lines1 != num_lines2:
                            lines_num_diff = ' file1 lines: {:d}, file2 lines: {:d}'.format(num_lines1, num_lines2)
                            lines_num_diff += ', file1>file2? ' + str(num_lines1>num_lines2)
                        diff_file.write(file_name1 + lines_num_diff + '\n')
                    elif num_lines1 !=0 :
                        same_non_empty_count += 1
    print('# of different files: {:d}/{:d}'.format(diff_count, total_count))
    print('# of identical non-empty files: {:d}/{:d}'.format(same_non_empty_count, total_count))

if __name__ == '__main__':
    in_dir1 = '/home/elad/Data/SeeingThroughFog/gt_labels/cam_left_labels_TMP'
    in_dir2 ='/home/elad/Data/SeeingThroughFog/gt_labels/gated_labels_TMP'
    out_dir1 = in_dir1.split('/')[-1]
    out_dir2 = in_dir2.split('/')[-1]
    gt_to_2dbox(in_dir1, out_dir1)
    gt_to_2dbox(in_dir2, out_dir2)
    compare_files(out_dir1, out_dir2)


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