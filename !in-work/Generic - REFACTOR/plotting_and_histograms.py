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


def make_mplots(mdf, limits, title, pstyle = 'ggplot'):
    ''' This function assumes multi dataframe has board-named columns '''
    print('Plotting temporal plot...', end ='')
    boards = get_bnums(mdf)  ## get boards used in test

    ## if possible, retrieve module names for each test station board
    if limits != None:
        real_lines = [ limits.boards_dict[board] for board in boards ]
    else:
        real_lines = [ "" for board in boards ]
    print("BOARDS:", boards)
    vsetpoint = mdf['VSetpoint ' + boards[0]]
    temps = [mdf.columns[i] for i in range(len(mdf.columns)) if re.search(REGEX_TEMPS_BNUMS(boards[0]), mdf.columns[i])]

    ### create plot space with appropriate num of subplots, also plot characteristics
    style.use(pstyle)  ## set formatting style to use for matplotlib
    fig, axes = plt.subplots(nrows=len(boards)+2, ncols=1, sharex=True, figsize=(15,11))  ## create plot space with app num of subplots
    fig.suptitle(title, fontsize = 20, fontweight= 'bold')  ## main title for entire figure
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
    aux_colors = ['#00A0A6', '#FFA500', '#DA70D6', '#E5E500', '#FDFD96', '#B22222']  ### TO DO make color dict for plotting (as global var)
    board_colors = dict(zip(boards, aux_colors))
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

    ## SUBPLOT(S) 3 (up to 6) : BOARD CURRENTS
    row = 2  ## start on third row subplot
    for board in boards:
        currents = [mdf.columns[i] for i in range(len(mdf.columns)) if re.search(REGEX_BNUMS(board), mdf.columns[i])]
        mdf[currents].plot(ax=axes[row])
        row +=1
    plt.gcf().autofmt_xdate()
    ### ---------------------------------------------------------------------- ###

    ## format legends for subplots
    line_labels = [ 'Vsense ' + line for line in real_lines ]
    line_labels.insert(0, 'VSetpoint')
    voltage_labels = axes[0].get_legend_handles_labels()[1]
    axes[0].legend(fontsize=8, loc='center left', bbox_to_anchor=(1.0, 0.5),
                   labels = line_labels)
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
            axes[i].legend_.remove()

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
    axes[1].set_ylabel(u"Temperature (\N{DEGREE SIGN}C)")
    axes[1].set_title("Temperature Profile")

    ## set fig size and save
    print('...complete.\n')
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



################################
###### HISTOGRAM FUNCTIONS ######
################################

def single_mode_hist(df, mask, limits, temp, title, directory, pstyle='ggplot'):
    ## allocate data
    bnums = get_bnums(df)  ## get boards present in mask dframe
    b_start = int(bnums[0][-1])  ## retrieve lowest test station board number
    on_off_dict = dict(zip(bnums, mask))
    boards = [board for board in bnums if on_off_dict[board]=='1']  ## only ON boards
    board = boards[0]
    systems = [df.columns[i] for i in range(len(df.columns)) if re.search(REGEX_BNUMS(board), df.columns[i])]
    if limits != None:
        real_line = limits.boards_dict[board]
    else:
        real_line = ""

    print('\t=>Histogram:', str(temp)+'C', str(real_line)+'...')

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
    extended_title = title + ': ' + str(real_line) + ' (' + str(board) +') only at ' + str(temp) + '\u00b0C'
    fig.suptitle(extended_title, fontsize = 14, fontweight='bold')
    plt.figtext(0.5, .935, 'Note: black line is sample mean, red dashed lines are lower and upper current limits, and blue dotted lines are \u00b110\u0025 of the mean',
                style='italic', fontsize=8, ha = 'center', va = 'top')
    nrows, ncols = len(voltages), 1
    i = 1
    plot_title = str(real_line) + ' only '+ str(temp)+'C'
    for v in voltages:
        data = volt_dict[v]
        avg = float(data.mean())
        LL, UL = limits.lim[temp][board][v][0], limits.lim[temp][board][v][1]
        minus_ten = round(avg*0.9, 3)
        plus_ten = round(avg*1.1, 3)
        ax = fig.add_subplot(nrows, ncols, i)
        ax.hist(data.dropna(), color='g')  ## drop NaN values
        ax.axvline(avg, color='k', linestyle='solid', linewidth=2)
        ax.axvline(LL, color='red', linestyle='dashed', linewidth=2)
        ax.axvline(UL, color='red', linestyle='dashed', linewidth=2)
        ax.axvline(minus_ten, color='b', linestyle='dotted', linewidth=2)
        ax.axvline(plus_ten, color='b', linestyle='dotted', linewidth=2)
        ax.set_xlabel('Current (A)', fontsize=8)
        ax.set_ylabel('Frequency', fontsize=8)
        plt.setp(ax.get_xticklabels(), fontsize=8)
        plt.setp(ax.get_yticklabels(), fontsize=8)
        ax.set_title(str(v)+'V   Avg: '+str(round(avg,3))+'   LowerLimit: '+str(LL)+'   UpperLimit: '+str(UL), fontsize=9)
        #ax.set_title( str(v)+'V   Avg: '+str(round(avg,3))+'   -10%: '+str(minus_ten)+'   +%10: '+str(plus_ten))
        #ax.set_title( str(v)+'V   Avg: '+str(round(avg,3))+'   LowerLimit: '+str(LL)+'   UpperLimit: '+str(UL) +'   -10%: '+str(minus_ten)+'   +%10: '+str(plus_ten))
        i += 1
    plt.tight_layout()
    plt.subplots_adjust(top=0.87, bottom=0.05, left=0.07, right=0.97)
    plt.savefig(directory + 'Hist ' + title + ' ' + plot_title + '.png', dpi = 400)
    print('\tcomplete.\n')

def multi_mode_hist(data_dict, mask, limits, temp, title, directory, pstyle='ggplot'):
    # print('IN MULTIMODE HIST FUNCTION')
    ## allocate data
    df = data_dict[mask]  ## get appropriate dataframe
    bnums = get_bnums(df)  ## get boards present in mask dframe
    b_start = int(bnums[0][-1])  ## find lowest test station board number
    on_off_dict = dict(zip(bnums, mask))
    boards = [board for board in bnums if on_off_dict[board]=='1']  ## only ON boards
    boards_wo6 = [board for board in boards if (board != 'B6')]  ## on_boards that are not outage
    bmode = ''.join(str(b) for b in sorted(boards) if b != 'B6')  ## string board combo
    systems_only = [df.columns[i][:-2] for i in range(len(df.columns)) if re.search(REGEX_BNUMS(boards[0]), df.columns[i])]
    systems_bmode = [sys+bmode for sys in systems_only]
    if limits != None:
        lines = [ limits.boards_dict[board] for board in boards ]
        if 'OUTAGE' in lines: lines.remove('OUTAGE')
        real_lines = "+".join(lines)
    else:
        real_lines = ""
    print('\t=>Histogram:', str(temp)+'C', str(real_lines)+'...')

    ## create multimode current columns -- NEED FOR MULTIMODE ANALYSIS
    for sys in systems_only:
        df[sys+bmode] = 0
        for b in boards:
            if b != 'B6':
                df[sys+bmode] = df[sys+bmode] + df[sys+b]

    temp_header = 'Amb Temp TC1 ' + boards[0]  ## need this to access temperature in df
    tolerance = TEMPERATURE_TOLERANCE ## temperature tolerance
    vsetpoint = 'VSetpoint ' + boards[0]
    voltages = sorted(set(df[vsetpoint]))  ## find voltages setpoints used in mode
    volt_dict = {}
    for voltage in voltages:
        voltage_dframe = df.loc[(df[vsetpoint] == voltage) &
                            (df[temp_header] > (temp-tolerance)) &
                            (df[temp_header] < (temp+tolerance))]
        dframe = pd.DataFrame()
        for sys in systems_bmode:
            dframe = pd.concat([ dframe, voltage_dframe[sys] ], ignore_index=True)
        volt_dict[voltage] = dframe
    ## plot histograms
    fig = plt.figure()
    style.use(pstyle)
    extended_title = title + ': ' + str(real_lines) + ' (' + str(bmode)+') at ' + str(temp) + '\u00b0C'
    fig.suptitle(extended_title, fontsize = 14, fontweight='bold')
    plt.figtext(0.5, .935, 'Note: black line is sample mean, red dashed lines are lower and upper current limits, and blue dotted lines are \u00b110\u0025 of the mean',
                style='italic', fontsize=8, ha = 'center', va = 'top')
    nrows, ncols = len(voltages), 1
    i = 1
    plot_title = str(real_lines) + ' ' + str(temp)+'C'
    for v in voltages:
        data = volt_dict[v]
        avg = float(data.mean())
        LL, UL = limits.lim[temp][bmode][v][0], limits.lim[temp][bmode][v][1]
        minus_ten = round(avg*0.9, 3)
        plus_ten = round(avg*1.1, 3)
        ax = fig.add_subplot(nrows, ncols, i)
        ax.hist(data.dropna(), color='g')  ## drop NaN values
        ax.axvline(avg, color='k', linestyle='solid', linewidth=2)
        ax.axvline(LL, color='red', linestyle='dashed', linewidth=2)
        ax.axvline(UL, color='red', linestyle='dashed', linewidth=2)
        ax.axvline(minus_ten, color='b', linestyle='dotted', linewidth=2)
        ax.axvline(plus_ten, color='b', linestyle='dotted', linewidth=2)
        ax.set_xlabel('Current (A)', fontsize = 8)
        ax.set_ylabel('Frequency', fontsize = 8)
        plt.setp(ax.get_xticklabels(), fontsize=8)
        plt.setp(ax.get_yticklabels(), fontsize=8)
        ax.set_title(str(v)+'V   Avg: '+str(round(avg,3))+'   LowerLimit: '+str(LL)+'   UpperLimit: '+str(UL), fontsize=9)
        #ax.set_title( str(v)+'V   Avg: '+str(round(avg,3))+'   -10%: '+str(minus_ten)+'   +%10: '+str(plus_ten))
        #ax.set_title( str(v)+'V   Avg: '+str(round(avg,3))+'   LowerLimit: '+str(LL)+'   UpperLimit: '+str(UL) +'   -10%: '+str(minus_ten)+'   +%10: '+str(plus_ten) )
        i += 1
    plt.tight_layout()
    plt.subplots_adjust(top=0.87, bottom=0.05, left=0.07, right=0.97)
    plt.savefig(directory + 'Hist ' + title + ' ' + plot_title + '.png', dpi = 400)
    print('\tcomplete.\n')

def histograms(data_dict, limits, outage_bool, temp, title):
    ''' Function to be used with GUI '''
    # print('IN HISTOGRAMS FUNC: "outage" is', outage)
    directory = r'!output//Histograms//'
    if not os.path.exists(directory):
        os.makedirs(directory)
    for mask in sort_masks(list(data_dict.keys()), outage_bool):
        if outage_bool:  ## outage ON
            if (mask.count('1') == 1) or ( outage_bool and (mask.count('1') == 2) and mask[-1] == '1' ):
                single_mode_hist(data_dict[mask], mask, limits, temp, title, directory)
            elif (mask.count('1') > 2) or ( outage_bool and (mask.count('1') == 2) and mask[-1] == '0' ):
                #if mask != '1010':  ## for establishing limits (don't allow turn w/o outage)
                multi_mode_hist(data_dict, mask, limits, temp, title, directory)
        else:  ## outage OFF
            if (mask.count('1') == 1):
                single_mode_hist(data_dict[mask], mask, limits, temp, title, directory)
            elif (mask.count('1') > 1):
                multi_mode_hist(data_dict, mask, limits, temp, title, directory)


def plot_histograms(filename_and_title, data_dict, limits, outage_bool, temps):
    print('Plotting histograms:\n')
    for temp in temps:
        histograms(data_dict, limits, outage_bool, temp, filename_and_title)