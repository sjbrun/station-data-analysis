#!/usr/bin/python3

''' This module contains functions that create current histograms using matplotlib. '''

import math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib import style


def system_histograms(test):
	print('Plotting histograms:\n')
	modes = test.mode_stats
	for mode in modes:
		for temp in mode.temps:
			for voltage in mode.voltages:
				histogram_of_mode(test, mode, temp, voltage)
	plt.show('hold') ## wait until all plots are built to show them

def histogram_of_mode(test, mode, temp, voltage):
    fig = plt.figure()
    title = ' '.join([mode.board_mode, str(temp), str(voltage)])
    fig.suptitle(title, fontsize = 14, fontweight='bold')
    nrows, ncols = 1, 1
    i = 1
    
    if len(mode.board_ids) > 1:
    	pass
    else:
	    current_data = mode.hist_dict[temp][voltage]
	    avg = float(current_data.mean())
	    minus_ten = round(avg*0.9, 3)
	    plus_ten = round(avg*1.1, 3)

	    ax = fig.add_subplot(nrows, ncols, i)
	    ax.hist(data.dropna(), color='g')  ## drop NaN values
	    ax.axvline(avg, color='k', linestyle='solid', linewidth=2)
	    ax.axvline(minus_ten, color='b', linestyle='dotted', linewidth=2)
	    ax.axvline(plus_ten, color='b', linestyle='dotted', linewidth=2)
	    ax.set_xlabel('Current (A)', fontsize=8)
	    ax.set_ylabel('Frequency', fontsize=8)
	    plt.setp(ax.get_xticklabels(), fontsize=8)
	    plt.setp(ax.get_yticklabels(), fontsize=8)

	    plt.tight_layout()

