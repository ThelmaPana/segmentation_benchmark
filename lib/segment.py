import numpy as np
import skimage.measure
from psd_tools import PSDImage


def split_psd(psd_file, min_area=50, alpha_threshold=100):
    """
    Split a psd image into mask and background; remove very small particles from mask and label mask.
    
    Args:
        psd_file (str): name of psd file
        min_area (int): minimum size of particles (default is 50)
        alpha_threshold (int): alpha value above which to consider particles (default is 100)
    
    Returns:
        back (1darray): background image
        mask_labelled_large (1darray): labelled mask without small particles
    """
    # read psd file
    psd = PSDImage.open(psd_file)
    
    ## Process background
    # extract back layer
    back = psd[0]
    # convert to numpy array
    back = back.numpy()
    
    #back = np.array(back.topil())
    
    # keep only one channel (they are all the same)
    back = back[:,:,0]
    # rotate back of 90° counter clockwise
    back = np.rot90(back)
    
    ## Process mask
    # extract mask layer
    mask = psd[1]
    # convert to numpy array
    mask = mask.numpy()
    # extract alpha channel of mask layer
    mask = mask[:, :, 3]
    # rotate mask of 90° counter clockwise
    mask = np.rot90(mask)
    # multiply by 255 and convert to int
    mask = (mask*255).astype(np.uint8)
    # threshold particles with alpha level
    mask = mask > alpha_threshold
    
    ## Remove very small particles (likely to be forgotten pixels)
    # label mask
    mask_labelled = skimage.measure.label(mask, background=False, connectivity=2)
    # recreate a labelled image with only large regions
    regions = skimage.measure.regionprops(mask_labelled)
    large_regions = [r for r in regions if fast_particle_area(r) > min_area]
    mask_labelled_large = np.zeros_like(mask_labelled)
    
    # create list of odd numbers for labels to avoid multiple particles with identical labels
    # If one particle is located inside another one, the sum of their label is an even number, different from every other label.
    n_large_regions = len(large_regions)
    labels = range(1, n_large_regions*2+1, 2)
    
    for i in range(n_large_regions):
        r = large_regions[i]
        mask_labelled_large[r._slice] = mask_labelled_large[r._slice] + labels[i]*r.filled_image
    
    return(back, mask_labelled_large)
 
def fast_particle_area(x):
    return(np.sum(x._label_image[x._slice] == x.label))


