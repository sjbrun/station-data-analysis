#!/usr/bin/python3

''' This module contains functions that create current histograms using matplotlib. '''

import math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib import style


def make_mode_histograms(test, system_by_system = True):
	print('Plotting histograms...\n')
	modes = test.mode_stats
	for mode in modes:
		for temp in mode.temps:
			for voltage in mode.voltages:
				if system_by_system:
					histogram_of_each_system(test, mode, temp, voltage)
				else:
					histogram_of_mode(test, mode, temp, voltage)
	print('complete.')
	plt.show('hold') ## wait until all plots are built to show them

def subplot_layout(num):
	nrows, ncols = 0, 0
	if num > 10:
		nrows, ncols = 3, 4
	elif num == 10:
		nrows, ncols = 2, 5
	elif num == 9:
		nrows, ncols = 3, 3
	elif num > 6:
		nrows, ncols = 2, 4
	elif num > 4:
		nrows, ncols = 2, 3
	elif num == 4:
		nrows, ncols = 2, 2
	else:
		nrows, ncols = 1, num	
	return nrows, ncols

def histogram_of_each_system(test, mode, temp, voltage):
	num_subplots = len(mode.systems)
	fig = plt.figure()
	title = ' '.join([mode.board_mode, str(temp), str(voltage)])
	fig.canvas.set_window_title(title)
	fig.suptitle(title, fontsize = 14, fontweight='bold')
	nrows, ncols = subplot_layout(num_subplots)
	i = 1
	for system in mode.systems:
		current_data = pd.to_numeric(mode.mode_df[system], downcast='float')
		ax = fig.add_subplot(nrows, ncols, i)
		ax.set_title(test.systems[i-1])
		ax.hist(current_data.dropna())  ## drop NaN values
		ax.set_xlabel('Current (A)')
		ax.set_ylabel('Frequency')
		ax.get_xaxis().get_major_formatter().set_useOffset(False)
		i += 1


def histogram_of_mode(test, mode, temp, voltage):
    fig = plt.figure()
    title = ' '.join([mode.board_mode, str(temp), str(voltage)])
    fig.suptitle(title, fontsize = 14, fontweight='bold')
    nrows, ncols = 1, 1
    
    i = 1
    current_data = mode.hist_dict[temp][voltage]
    avg = current_data.mean()
    minus_ten = round(avg*0.9, 3)
    plus_ten = round(avg*1.1, 3)
  
    ax = fig.add_subplot(nrows, ncols, i)
    ax.hist(current_data.dropna(), color='g')  ## drop NaN values
    ax.axvline(avg, color='k', linestyle='solid', linewidth=2)
    ax.axvline(minus_ten, color='b', linestyle='dotted', linewidth=2)
    ax.axvline(plus_ten, color='b', linestyle='dotted', linewidth=2)
    ax.set_xlabel('Current (A)', fontsize=8)
    ax.set_ylabel('Frequency', fontsize=8)
    plt.setp(ax.get_xticklabels(), fontsize=8)
    plt.setp(ax.get_yticklabels(), fontsize=8)

    plt.tight_layout()

