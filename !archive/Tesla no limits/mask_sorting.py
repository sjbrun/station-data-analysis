#!/usr/bin/python3

''' This module contains functions that determine which modes were 
excited for the selected test data. '''

###### MASK FUNCTIONS ######

def sort_outage_on(mask_list):
## masks (modes) sorting function if outage is ON 
    master = []
    most_on = 0
    masks_copy = [m[:-1] for m in mask_list]
    ## find mask with mosts 1's
    for m in masks_copy:
        num_on = m.count('1')
        if num_on > most_on:
            most_on = num_on ## most on boards that are not outage
    ## start with single modes and move to multimodes
    for num in range(1, most_on+1):
        level = [] ## holds level of modes
        for m in mask_list.copy():
            mask = m[:-1]
            if mask.count('1') == num:
                level.append(m)
                mask_list.remove(m)
        level.sort(reverse=True)
        master.extend(level)
    return master

def sort_outage_off(mask_list):
## masks (modes) sorting function if outage is OFF 
    master = []
    most_on = 0
    ## find mask with mosts 1's
    for m in mask_list:
        num_on = m.count('1')
        if num_on > most_on:
            most_on = num_on
    for num in range(1, most_on+1):
        level = []
        for m in mask_list.copy():
            if m.count('1') == num:
                level.append(m)
                mask_list.remove(m)
        level.sort(reverse=True)
        master.extend(level)
    return master

def sort_masks(mask_list, outage):
    if outage: ## if outage is ON
        return sort_outage_on(mask_list)
    else:  ## outage is OFF
        return sort_outage_off(mask_list)