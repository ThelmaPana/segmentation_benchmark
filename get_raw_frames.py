#!/usr/bin/python3
# coding: utf-8

#--------------------------------------------------------------------------#
# Project: segmentation_benchmark
# Script purpose: Extract raw frames from avi files for benchmark images
# Date: 28/10/2021
# Author: Thelma Panaiotis
#--------------------------------------------------------------------------#

import glob
import cv2
import os
import pandas as pd
import tarfile


## Settings
# avi files directory 
target = '/remote/complex/tpanaiotis/raw_visufront/cross_current_7/'

# create directory to store raw frames
os.makedirs('data/raw_frames', exist_ok=True)

# initiate empty dataframe to store avi names and frames
avi_frames = pd.DataFrame()


## List avi files and frames to extract, this is found in properties of regular particles
tar_files = glob.glob('data/regular_apeep_def/particles/*.tar')
tar_files.sort()
print(f'Found {len(tar_files)} tar files to process')

# Loop over tar files, open tsv table with properties, extract avi file and frame nb
for f in tar_files:

    # open tar archive in read mode
    arch = tarfile.open(f, mode = 'r')
    
    # get name of tsv file
    tsv_file = [x for x in arch.getnames() if 'tsv' in x][0]
    
    # read tsv file and keep only position in avi file
    pos = pd.read_csv(arch.extractfile(tsv_file), sep = '\t', comment = '[', dtype={'object_time': str, 'object_date': str})[['acq_id', 'object_avi_file', 'object_frame_nb']]
    
    # keep unique rows (should be 5 per image because 5 frames per image)
    pos = pos.drop_duplicates().reset_index(drop=True)
    
    # Append rows to table of all frames and avi
    avi_frames = pd.concat([avi_frames, pos]).sort_values('object_frame_nb').reset_index(drop=True)
    
    # Close tar archive
    arch.close()

# rename columns
avi_frames = avi_frames.rename(columns={'acq_id': 'img_name', 'object_avi_file': 'avi_file', 'object_frame_nb': 'frame_nb'})

# Check that 5 frames are present for each image
frames_per_img = avi_frames.groupby('img_name').count()['frame_nb'].tolist()
assert all([x == 5 for x in frames_per_img]), 'At least one image does not have 5 frames'


## Open avi files and extract relevant frames
# List avi files
avi_files = avi_frames['avi_file'].drop_duplicates().tolist()
avi_files.sort()

# Join with path to avi files directory
avi_files = [os.path.join(target, f) for f in avi_files]

# Loop over avi files
for avi in avi_files:

    # Get relevant frames for this file
    frames = avi_frames[avi_frames['avi_file'] == os.path.basename(avi)]['frame_nb'].tolist()
    
    # open file and reset frame counter
    cap = cv2.VideoCapture(avi)
    
    # loop over frames to process
    for i in frames:
        # go to frame i
        cap.set(1, i)
        # read frame
        ret, frame = cap.read()
        # save frame
        frame_name = os.path.basename(avi) + '_frame_' + str(i) + '.png'
        cv2.imwrite(os.path.join('data/raw_frames', frame_name), frame)
    
    # Close avi file
    cap.release()

print('Finished')
