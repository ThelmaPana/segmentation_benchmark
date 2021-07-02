#--------------------------------------------------------------------------#
# Project: segmentation_benchmark
# Script purpose: Process manual stacks: extract and measure particles for Ecotaxa import, generate segmented images
# Date: 19/04/2021
# Author: Thelma Panaiotis
#--------------------------------------------------------------------------#

import numpy as np
import glob
import os
import matplotlib.pyplot as plt
import tarfile
import shutil

# Import modified apeep scripts (https://github.com/jiho/apeep)
import lib.configure as configure
import lib.im_opencv as im
import lib.segment as segment
import lib.measure as measure

#from importlib import reload


## Read from apeep config file for regular segmentation
project_dir = 'data/regular_apeep'
cfg = configure.configure(project_dir)
transect_name = cfg['io']['input_dir'].split('/')[-1] if len(cfg['io']['input_dir'].split('/')[-1]) > 0 else cfg['io']['input_dir'].split('/')[-2]
img_width = 2048

## Manual data
# path to manual data dir
manual_dir = 'data/manual'
# path to manual stacks
stack_image_dir = os.path.join(manual_dir, 'manual_stacks')
# list of manual stacks to process
man_stacks = glob.glob(os.path.join(stack_image_dir, '*/Sans titre.psd'))
man_stacks.sort()

# Loop over manual stacks to process
for i,psd_file in enumerate(man_stacks):
#psd_file = man_stacks[0]

    # Extract image name
    img_name = psd_file.split('/')[-2]
    
    # Extract back and mask from psd image
    back, mask = segment.split_psd(psd_file, min_area = 20, alpha_threshold = 100)
    #plt.figure(figsize = (20, 20));plt.imshow(back, cmap ='gray' ); plt.show()
    
    # Extract back and mask from original psd image
    back_orig, _ = segment.split_psd(psd_file.replace('Sans titre', 'frame'), min_area = 20, alpha_threshold = 100)
    #plt.figure(figsize = (20, 20));plt.imshow(back_orig, cmap ='gray' ); plt.show()
    
    # If back from original and corrected images are different, vertically flip both corrected back and mask
    # NB: vertical flip because 'split_psd' function rotates back and mask of 90° counter clockwise
    if not (back_orig == back).all():
        back = np.flipud(back)
        mask = np.flipud(mask)    
        print(f'Flipping image {img_name}')
    
    # Write mask
    segmented_image_dir = os.path.join(manual_dir, 'segmented')
    os.makedirs(segmented_image_dir, exist_ok=True)
    #measure.write_segmented(mask, os.path.join(segmented_image_dir, img_name + '.png'))
    im.save(mask == 0, os.path.join(segmented_image_dir, img_name + '.png'))
    
    # Extract particles and their properties
    particles, particles_props = measure.measure(
        img = back, 
        img_labelled = mask, 
        img_name = img_name, 
        sample_id = transect_name, 
        props = cfg['measure']['properties']
    )
    
    # Write particles and properties
    particles_images_dir = os.path.join(manual_dir, 'particles', img_name)
    os.makedirs(particles_images_dir, exist_ok=True)
    
    # write particles images
    measure.write_particles(particles, particles_images_dir, px2mm=cfg['acq']['window_height_mm']/img_width)      
    # and properties
    measure.write_particles_props(particles_props, particles_images_dir)
    
    
    ## Create a tar archive containing particles and properties 
    #with tarfile.open(particles_images_dir + '.tar', 'w') as tar:
    #    tar.add(particles_images_dir, arcname=os.path.basename(particles_images_dir))
    #    tar.close()
    
    # Delete directory 
    #shutil.rmtree(particles_images_dir)
    print(f'Done image {img_name}')

    # Progress flag
    if (i+1)%10==0:
        print(f'Done with {i+1} out of {len(man_stacks)}')