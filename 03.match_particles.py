#!/usr/bin/env python
# coding: utf-8

#--------------------------------------------------------------------------#
# Project: segmentation_benchmark
# Script purpose: Match manual particles with those from apeep regular and semantic
# Date: 20/04/2021
# Author: Thelma Panaiotis
#--------------------------------------------------------------------------#



import os
import glob
import pandas as pd
import numpy as np
import math
import cv2
import matplotlib.pyplot as plt
import skimage.measure
import tarfile

import lib.measure as measure
import lib.im_opencv as im
import lib.matching as matching

#from importlib import reload

## Sets paths to data
manual_dir = 'data/manual' # path to manual data dir
reg_apeep_dir = 'data/regular_apeep' # path to regular apeep data dir
sem_apeep_dir = 'data/semantic_apeep' # path to semantic apeep data dir

## Output directory
output_dir = 'data/matches_bbox'
os.makedirs(output_dir, exist_ok=True)


# Initiate empty dict to store matches
# with regular particles
matches_reg = {
    'img_name': [],
    'man_ids': [],
    'reg_ids': [],
    'bbox_iou': [],
}
# with semantic particles
matches_sem = {
    'img_name': [],
    'man_ids': [],
    'sem_ids': [],
    'bbox_iou': [],
}

# Initiate empty dataframes to store all particles props
all_man_particles_props = pd.DataFrame()
all_reg_particles_props = pd.DataFrame()
all_sem_particles_props = pd.DataFrame()


# List segmented images to process
man_segments = glob.glob(os.path.join(manual_dir, 'segmented', '*'))
man_segments.sort()

# Read ecotaxa export with objects taxo
eco_exp = pd.read_csv('data/manual/02.ecotaxa_export_test_set.csv')
# rename colums
eco_exp = eco_exp.rename(columns = {
    'object_id': 'object_id',
    'img_name': 'acq_id',
    'bbox0': 'object_bbox-0',
    'bbox1': 'object_bbox-1',
    'bbox2': 'object_bbox-2',
    'bbox3': 'object_bbox-3'
}).drop('area', axis=1)



# Loop over segmented images
for en, img_path in enumerate(man_segments):
    # get image name
    img_name = os.path.split(img_path)[-1]
    
    # Read background image
    back = im.read(os.path.join(reg_apeep_dir, 'enhanced', img_name))
    #plt.figure(figsize = (20, 20)); plt.imshow(back, cmap = 'gray'); plt.show()
    
    ## Manual particles
    # read manual mask
    man_mask = im.read_mask(img_path)
    
    #man_particles_props = eco_exp[eco_exp['acq_id'] == img_name.replace('.png','')].reset_index(drop = True)
    ## extract particles and their properties
    man_particles, man_particles_props = measure.measure(
        img = back, 
        img_labelled = man_mask, 
        img_name = img_name.replace('.png',''), 
        sample_id = '', 
        props = ['label', 'bbox', 'area']
    )
    # drop useless columns
    man_particles_props = man_particles_props[['acq_id', 'object_label', 'object_bbox-0', 'object_bbox-1', 'object_bbox-2', 'object_bbox-3', 'object_area']]
    # join with ecotaxa taxonomy based on bbox and acq_id (image name)
    man_particles_props = man_particles_props.merge(eco_exp)
    # add to all manual particles props
    all_man_particles_props = pd.concat([all_man_particles_props, man_particles_props])
    
    # read regular apeep mask
    reg_mask = im.read_mask(os.path.join(reg_apeep_dir, 'segmented', img_name))
    # extract particles and their properties
    reg_particles, reg_particles_props = measure.measure(
        img = back, 
        img_labelled = reg_mask, 
        img_name = img_name.replace('.png',''), 
        sample_id = '', 
        props = ['label', 'bbox', 'area']
    )
    # compute bbox diagonal
    reg_particles_props['diag_bbox'] = np.sqrt((reg_particles_props['object_bbox-2'] - reg_particles_props['object_bbox-0'])**2 + \
    (reg_particles_props['object_bbox-3'] - reg_particles_props['object_bbox-1'])**2)
    # drop useless columns
    reg_particles_props = reg_particles_props[['object_id', 'acq_id', 'object_label', 'object_bbox-0', 'object_bbox-1', 'object_bbox-2', 'object_bbox-3', 'object_area', 'diag_bbox']]
    ## add to all regular particles props
    all_reg_particles_props = pd.concat([all_reg_particles_props, reg_particles_props])
   

    ## Semantic apeep particles
    # read semantic apeep mask
    sem_mask = im.read_mask(os.path.join(sem_apeep_dir, 'segmented', img_name))
    # extract particles and their properties
    sem_particles, sem_particles_props = measure.measure(
        img = back, 
        img_labelled = sem_mask, 
        img_name = img_name.replace('.png',''), 
        sample_id = '', 
        props = ['label', 'bbox', 'area']
    )
    # compute bbox diagonal
    sem_particles_props['diag_bbox'] = np.sqrt((sem_particles_props['object_bbox-2'] - sem_particles_props['object_bbox-0'])**2 + \
    (sem_particles_props['object_bbox-3'] - sem_particles_props['object_bbox-1'])**2)
    # drop useless columns
    sem_particles_props = sem_particles_props[['object_id', 'acq_id', 'object_label', 'object_bbox-0', 'object_bbox-1', 'object_bbox-2', 'object_bbox-3', 'object_area', 'diag_bbox']]
    # add to all semantic particles props
    all_sem_particles_props = pd.concat([all_sem_particles_props, sem_particles_props])


    # Loop over manual particles
    for i in man_particles_props.index:
    
        # get manual particle label, id and bbox
        man_label = man_particles_props.loc[i, 'object_label']
        man_id    = man_particles_props.loc[i, 'object_id']
        man_bb0   = man_particles_props.loc[i, 'object_bbox-0']
        man_bb1   = man_particles_props.loc[i, 'object_bbox-1']
        man_bb2   = man_particles_props.loc[i, 'object_bbox-2']
        man_bb3   = man_particles_props.loc[i, 'object_bbox-3']
        
        man_bb = [man_bb0, man_bb1, man_bb2, man_bb3]
        
        ## Look for match with regular particles
        # loop over regular particles
        for j in reg_particles_props.index:
            # get regular particle label, id and bbox
            reg_label = reg_particles_props.loc[j, 'object_label']
            reg_id    = reg_particles_props.loc[j, 'object_id']
            reg_bb0   = reg_particles_props.loc[j, 'object_bbox-0']
            reg_bb1   = reg_particles_props.loc[j, 'object_bbox-1']
            reg_bb2   = reg_particles_props.loc[j, 'object_bbox-2']
            reg_bb3   = reg_particles_props.loc[j, 'object_bbox-3']
            
            reg_bb = [reg_bb0, reg_bb1, reg_bb2, reg_bb3]
            
            # check for bbox intercept
            bbox_intersect = matching.check_bbox_overlap(man_bb, reg_bb)
            
            # compute bbox iou
            bbox_iou = matching.bbox_iou(man_bb, reg_bb)
            
            if bbox_iou > 0.1 :  
                # if bbox iou is > 0.1, save particles ids
                matches_reg['img_name'].append(img_name.replace('.png',''))
                matches_reg['man_ids'].append(man_id)
                matches_reg['reg_ids'].append(reg_id)
                matches_reg['bbox_iou'].append(bbox_iou)
                    
        ## Look for match with semantic particles
        # loop over semantic particles 
        for j in sem_particles_props.index:
            # get semantic particle label, id and bbox
            sem_label = sem_particles_props.loc[j, 'object_label']
            sem_id    = sem_particles_props.loc[j, 'object_id']
            sem_bb0   = sem_particles_props.loc[j, 'object_bbox-0']
            sem_bb1   = sem_particles_props.loc[j, 'object_bbox-1']
            sem_bb2   = sem_particles_props.loc[j, 'object_bbox-2']
            sem_bb3   = sem_particles_props.loc[j, 'object_bbox-3']
            
            sem_bb = [sem_bb0, sem_bb1, sem_bb2, sem_bb3]
            
            # check for bbox intercept
            bbox_intersect = matching.check_bbox_overlap(man_bb, sem_bb)
            
            # compute bbox iou
            bbox_iou = matching.bbox_iou(man_bb, sem_bb)

            if bbox_iou > 0.1 :  
                # if bbox iou is > 0.1, save particles ids
                matches_sem['img_name'].append(img_name.replace('.png',''))
                matches_sem['man_ids'].append(man_id)
                matches_sem['sem_ids'].append(sem_id)
                matches_sem['bbox_iou'].append(bbox_iou)
    
    # Progress flag
    print(f'{img_name} done')
    if (en+1)%10 == 0:
        print(f'Done with {en+1} out of {len(man_segments)}')
    

# when all images are processed, convert to a dataframe
matches_reg = pd.DataFrame(matches_reg)
matches_sem = pd.DataFrame(matches_sem)

# reorder columns in manual properties
all_man_particles_props = all_man_particles_props.reindex(columns=(['object_id'] + list([a for a in all_man_particles_props.columns if a != 'object_id']) ))

## Write all dataframes
# particles
all_man_particles_props.to_csv(os.path.join(output_dir, 'man_particles_props.csv'), index = False)
all_reg_particles_props.to_csv(os.path.join(output_dir, 'reg_particles_props.csv'), index = False)
all_sem_particles_props.to_csv(os.path.join(output_dir, 'sem_particles_props.csv'), index = False)
# matches
matches_reg.to_csv(os.path.join(output_dir, 'matches_reg.csv'), index = False)
matches_sem.to_csv(os.path.join(output_dir, 'matches_sem.csv'), index = False)




