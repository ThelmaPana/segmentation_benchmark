def check_bbox_overlap(bb1, bb2):
    """
    Check if two bbox overlap or not.
    Args:
        bb1 (list): coordinates of 1st bbox as [x1, y1, x2, y2] 
            The (x1, y1) position is at the top left corner,
            the (x2, y2) position is at the bottom right corner
        bb2 (list): coordinates of 2nd bbox as [x1, y1, x2, y2] 
            The (x1, y1) position is at the top left corner,
            the (x2, y2) position is at the bottom right corner
    Returns:
        bool: TRUE if there is an intersection, FALSE if not
    """
    # Determine the coordinates of the intersection rectangle
    x_left   = max(bb1[0], bb2[0])
    y_top    = max(bb1[1], bb2[1])
    x_right  = min(bb1[2], bb2[2])
    y_bottom = min(bb1[3], bb2[3])

    if x_right < x_left or y_bottom < y_top:
        inter = False
    else:
        inter = True
    
    return(inter)