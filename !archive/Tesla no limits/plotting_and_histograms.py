#!/usr/bin/python3

''' This module contains functions that create temporal plots and current histograms
using matplotlib. '''

from regular_expressions_and_globals import *
from mask_sorting import *
from dataframe_building import get_bnums

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib import style

################################
###### PLOTTING FUNCTIONS ######
################################

# def make_plot(df):
#     style.use('ggplot')
#     temps = [df.columns[i] for i in range(len(df.columns)) if ('TC' in df.columns[i])]
#     currents = [df.columns[i] for i in range(len(df.columns)) if re.search(REGEX_SYSTEMS, df.columns[i])]
#     fig, axes = plt.subplots(nrows=2, ncols=1, sharex=True)
#     df[currents].plot(ax=axes[0])
#     df[temps].plot(ax=axes[1])
#     for i in range(len(axes)):
#         axes[i].legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
#     plt.show('hold')

# def make_plots(*dfs):
#     print('Plotting...')
#     boards = []
#     for df in dfs:
#         boards.append(get_bnum(df))
#     style.use('ggplot')
#     vsetpoint = dfs[0]['VSetpoint '+boards[0]]
#     temps = [dfs[0].columns[i] for i in range(len(dfs[0].columns)) if ('TC' in dfs[0].columns[i])]
#
#     fig, axes = plt.subplots(nrows=len(dfs)+2, ncols=1, sharex=True)
#     vsetpoint.plot(ax=axes[0])
#     dfs[0][temps].plot(ax=axes[1])
#
#     row = 2  ## start on row 2
#     for df in dfs:
#         currents = [df.columns[i] for i in range(len(df.columns)) if re.search(REGEX_SYSTEMS, df.columns[i])]
#         df[currents].plot(ax=axes[row])
#         row +=1
#
#     for i in range(len(boards)+2):
#         if i < 2:
#             leg_labels = axes[i].get_legend_handles_labels()[1]
#             axes[i].legend(loc='center left', bbox_to_anchor=(1.0, 0.5),
#                            labels = [x[:-3] for x in leg_labels])
#         elif i == 2:
#             vert = {1:0.5, 2:-0.25 , 3:-1.0 , 4:-1.75 , 5:-2.5 , 6:-3.25}
#             leg_labels = axes[i].get_legend_handles_labels()[1]
#             axes[i].legend(loc='center left', bbox_to_anchor=(1.0, vert[len(boards)]),
#                            labels = [x[:-3] for x in leg_labels])
#         else:
#             axes[i].legend_.remove()
#
#     for i in range(len(boards)):
#         axes[i+2].set_title(boards[i])
#         if boards[i] == 'B6':
#             axes[i+2].set_ylabel("Voltage (V)")
#         else:
#             axes[i+2].set_ylabel("Current (A)")
#     axes[0].set_ylabel("Voltage (V)")
#     axes[0].set_ylim([0,20])
#     axes[1].set_ylabel(u"Temperature (\N{DEGREE SIGN}C)")
#
#     print('...complete.')
#     plt.show()


def make_mplots(mdf, limits, title, pstyle = 'ggplot'):
    ''' This function assumes multi dataframe has board-named columns '''

    print('Plotting...', end ='')
    boards = get_bnums(mdf)  ## get boards used in test

    ## if possible, retrieve module names for each test station board
    if limits != None:
        real_lines = [ limits.boards_dict[board] for board in boards ]
    else:
        real_lines = [ "" for board in boards ]
    print("M_MPLOTS BOARDS:", boards)

    style.use(pstyle)  ## set formatting style to use for matplotlib
    vsetpoint = mdf['VSetpoint ' + boards[0]]
    temps = [mdf.columns[i] for i in range(len(mdf.columns)) if re.search(REGEX_TEMPS_BNUMS(boards[0]), mdf.columns[i])]

    ### create plot space with appropriate num of subplots, also plot characteristics
    fig, axes = plt.subplots(nrows=len(boards)+2, ncols=1, sharex=True, figsize=(15,11))
    fig.suptitle(title, fontsize=20, fontweight='bold')  ## main title for entire figure
    plt.tight_layout()

    ### ---------------------------------------------------------------------- ###
    ### Set up datetime format for x-axis label and start subplot 1 with VSetpoint
    axes[0].plot_date(mdf.index.to_pydatetime(), vsetpoint, 'k--', linewidth=3, zorder=10)
    date_fmt = '%m/%d/%y %H:%M:%S'
    formatter = dates.DateFormatter(date_fmt)
    locator = dates.AutoDateLocator()
    axes[0].xaxis.set_major_formatter(formatter)
    axes[0].xaxis.set_major_locator(locator)

    ### ---------------------------------------------------------------------- ###
    ## SUBPLOT 1: VOLTAGE AND FUNCTIONAL CYCLE
    tesla_colors = ['#FFFFCC', '#800080', '#FF4646', '#8B4513', '#FFA500', '#C0C0C0']
    board_colors = dict(zip(boards, tesla_colors))
    for board in boards:
        if '6' in board:
            continue
        vsense = [mdf.columns[i] for i in range(len(mdf.columns)) if re.search(REGEX_VSENSE1(board), mdf.columns[i])]
        if '5' in board:
            mdf[vsense].plot(ax=axes[0], color=board_colors[board], linewidth=2, linestyle = ':')
        else:
            mdf[vsense].plot(ax=axes[0], color=board_colors[board], linewidth=2)

    ## SUBPLOT 2: TEMPERATURES
    mdf[temps].plot(ax=axes[1])

    ## SUBPLOT(S) 3 (up to 6) : BOARD CURRENTS (and OUTAGE)
    row = 2  ## start on third row subplot
    for board in boards:
        currents = [mdf.columns[i] for i in range(len(mdf.columns)) if re.search(REGEX_BNUMS(board), mdf.columns[i])]
        mdf[currents].plot(ax=axes[row])
        if board == 'B6':
            axes[row].set_ylim([0,20])
        row +=1
    plt.gcf().autofmt_xdate()
    ### ---------------------------------------------------------------------- ###

    ## format legends for subplots
    line_labels = [ 'Vsense ' + line for line in real_lines ]
    line_labels.insert(0, 'VSetpoint')
    voltage_labels = axes[0].get_legend_handles_labels()[1]
    axes[0].legend(fontsize=8, loc='center left', bbox_to_anchor=(1.0, 0.5), labels = line_labels)
    for i in range(len(boards)+2):
        if i == 0:
            continue
        if i < 2:
            leg_labels = axes[i].get_legend_handles_labels()[1]
            axes[i].legend(fontsize=8, loc='center left', bbox_to_anchor=(1.0, 0.5),
                           labels = [x[:-3] for x in leg_labels])
        elif i == 2:
            vert = {1:0.5, 2:-0.25 , 3:-1.0 , 4:-1.75 , 5:-2.5 , 6:-3.25} ## where to place legend based on number of boards
            leg_labels = axes[i].get_legend_handles_labels()[1]
            axes[i].legend(fontsize=8, loc='center left', bbox_to_anchor=(1.0, vert[len(boards)]),
                           labels = [x[:-3] for x in leg_labels])
        else:
            try:
                axes[i].legend_.remove()
            except AttributeError as e:
                print(e)

    ## add labels/titles/plt_range to subplots and axes
    for i in range(len(boards)):
        axes[i+2].set_title(real_lines[i] + ' (' + boards[i] + ')')
        if boards[i] == 'B6':
            axes[i+2].set_ylabel("Voltage (V)")
        else:
            axes[i+2].set_ylabel("Current (A)")
    axes[0].set_ylabel("Voltage (V)")
    axes[0].set_ylim([0,20])
    axes[0].set_title("Voltage and Functional Cycle")
    axes[1].set_ylabel(u"Temp (\N{DEGREE SIGN}C)")
    axes[1].set_title("Temperature Profile")

    ## set fig size and save
    print('...complete.')
    fig.subplots_adjust(top=0.90, bottom=0.11, left=0.06, right=0.90, hspace=0.33)
    plt.savefig('!output//' + title + ' - temporal plot.png', dpi = 400)

def plot_all(folder):
    mdf = mother_dataframe(folder)
    make_mplots(mdf)

def plot_select(folder, b_nums, pstyle='ggplot'):
    ''' Plot b_nums from folder
        (e.g. - type in 135 to see boards 1, 3, and 5 '''
    b_nums= str(b_nums)
    boards = sorted(['B'+num for num in b_nums])
    mdf = build_select_df(folder, *boards)
    make_mplots(mdf, pstyle)

def plot_current_select(folder, b_nums, pstyle='ggplot'):
    ''' Plot b_nums from folder
        (e.g. - type in 135 to see boards 1, 3, and 5 '''
    b_nums= str(b_nums)
    boards = sorted(['B'+num for num in b_nums])
    mdf = build_select_df(folder, *boards)
    make_mcurrent_plots(mdf, pstyle)


#################################
###### HISTOGRAM FUNCTIONS ######
#################################

def make_hist(df, board, limits, temp, title, directory, pstyle='ggplot'):
    ## allocate data
    print('IN HIST FUNCTION')
    bnums = get_bnums(df)  ## get boards present in mask dframe
    b_start = int(bnums[0][-1])  ## retrieve lowest test station board number
    systems = [df.columns[i] for i in range(len(df.columns)) if re.search(REGEX_BNUMS(board), df.columns[i])]
    if limits != None:
        real_line = limits.boards_dict[board]
    else:
        real_line = ""
    temp_header = 'Amb Temp TC1 ' + board
    tolerance = TEMPERATURE_TOLERANCE ## temperature tolerance
    vsetpoint = 'VSetpoint ' + board
    voltages = sorted(set(df[vsetpoint]))  ## find voltages setpoints used in mode
    volt_dict = {}
    for voltage in voltages:
        voltage_dframe = df.loc[(df[vsetpoint] == voltage) &
                            (df[temp_header] > (temp-tolerance)) &
                            (df[temp_header] < (temp+tolerance))]
        dframe = pd.DataFrame()
        for sys in systems:
            dframe = pd.concat([ dframe, voltage_dframe[sys] ], ignore_index=True)
        volt_dict[voltage] = dframe
    ## plot histograms
    fig = plt.figure()
    style.use(pstyle)
    plot_title = str(real_line) + ' ' + str(temp) + u'\N{DEGREE SIGN}' + 'C'
    fig.suptitle(title + ': ' + plot_title, fontsize = 14, fontweight='bold')
    plt.figtext(0.5, .935, 'Note: black line is sample mean, red dashed lines are lower/upper current limits, and blue dotted lines are \u00b110\u0025 of the mean', style='italic', fontsize=8, ha = 'center', va = 'top')
    nrows, ncols = len(voltages), 1
    i = 1

    for v in voltages:
        data = volt_dict[v]
        avg = float(data.mean())
        LL, UL = limits.lim[temp][board][v][0], limits.lim[temp][board][v][1]
        minus_ten = round(avg*0.9, 3)
        plus_ten = round(avg*1.1, 3)
        ax = fig.add_subplot(nrows, ncols, i)
        ax.hist(data.dropna(), color='g')  ## drop NaN values
        ax.axvline(avg, color='k', linestyle='solid', linewidth=2)
        #ax.axvline(LL, color='red', linestyle='dashed', linewidth=2)
        #ax.axvline(UL, color='red', linestyle='dashed', linewidth=2)
        ax.axvline(minus_ten, color='b', linestyle='dotted', linewidth=2)
        ax.axvline(plus_ten, color='b', linestyle='dotted', linewidth=2)
        ax.set_xlabel('Current (A)', fontsize = 8)
        ax.set_ylabel('Frequency', fontsize = 8)
        plt.setp(ax.get_xticklabels(), fontsize=8)
        plt.setp(ax.get_yticklabels(), fontsize=8)
        ax.set_title( str(v)+'V   Avg: '+str(round(avg,3))+'   LowerLimit: '+str(LL)+'   UpperLimit: '+str(UL)+ '   -10%: '+str(minus_ten)+'   +%10: '+str(plus_ten), fontsize = 9)
        i += 1
    plt.tight_layout()
    plt.subplots_adjust(top=0.87, bottom=0.08, left=0.07, right=0.97)
    plt.savefig(directory + 'Hist ' + title + ' ' + plot_title + '.png', dpi = 400)
    # plt.savefig(directory + 'Hist ' + title + ' ' + plot_title + '.png', dpi = 400, bbox_inches='tight')

def histograms(mdf, limits, temp, title):
    ''' Function to be used with GUI '''
    directory = '!output//Histograms//'
    if not os.path.exists(directory):
        os.makedirs(directory)
    boards = get_bnums(mdf)  ## get boards present mother dframe
    for board in boards:
        if board != 'B6':  ## if board is not outage
            board_on_off = 'Board on/off ' + board
            board_df = mdf.loc[(mdf[board_on_off] == 1)]  ## set dataframe to only when board is ON
            make_hist(board_df, board, limits, temp, title, directory)
