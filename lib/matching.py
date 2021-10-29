def check_bbox_overlap(bb_a, bb_b):
    """
    Check if two bbox overlap or not.
    Args:
        bb_a (list): coordinates of 1st bbox as [bb0, bb1, bb2, bb3] 
        bb_b (list): coordinates of 2nd bbox as [bb0, bb1, bb2, bb3] 
            The (bb0, bb1) position is at the top left corner,
            the (bb2, bb3) position is at the bottom right corner
    
                    bb1                bb3

        bb0          +------------------+
                     |                  |
                     |                  |
                     |                  |
        bb2          +------------------+


    Returns:
        bool: TRUE if there is an intersection, FALSE if not
    """
    # Determine the coordinates of bbox intersection
    bb_top    = max(bb_a[0], bb_b[0])
    bb_left   = max(bb_a[1], bb_b[1])
    bb_bottom = min(bb_a[2], bb_b[2])
    bb_right  = min(bb_a[3], bb_b[3])

    if bb_right < bb_left or bb_bottom < bb_top:
        inter = False
    else:
        inter = True
    
    return(inter)


def bbox_iou(bb_a, bb_b):
    """
    Compute the intersection over union (iou) of two bbox. 
    Args:
        bb_a (list): coordinates of 1st bbox as [bb0, bb1, bb2, bb3] 
        bb_b (list): coordinates of 2nd bbox as [bb0, bb1, bb2, bb3] 
            The (bb0, bb1) position is at the top left corner,
            the (bb2, bb3) position is at the bottom right corner
    
                    bb1                bb3

        bb0          +------------------+
                     |                  |
                     |                  |
                     |                  |
        bb2          +------------------+


    Returns:
        float: bbox iou value
    """
    # Determine the coordinates of bbox intersection
    bb_top    = max(bb_a[0], bb_b[0])
    bb_left   = max(bb_a[1], bb_b[1])
    bb_bottom = min(bb_a[2], bb_b[2])
    bb_right  = min(bb_a[3], bb_b[3])

    # Case of no intersection between bbox
    if bb_right < bb_left or bb_bottom < bb_top:
        iou = 0

    # Case of intersection between bbox    
    else:
        # Compute the intersection area
        area_inter = (bb_right - bb_left) * (bb_bottom - bb_top)
        
        # Compute area of both bbox
        area_bb_a = (bb_a[2] - bb_a[0]) * (bb_a[3] - bb_a[1])
        area_bb_b = (bb_b[2] - bb_b[0]) * (bb_b[3] - bb_b[1])
        
        # Compute the union area as the sum of bbox area minus the intersection area
        area_union = area_bb_a + area_bb_b - area_inter
        
        # Compute value of iou
        iou = area_inter / area_union
    
    return(iou)

