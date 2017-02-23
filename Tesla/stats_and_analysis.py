#!/usr/bin/python3

''' This module contains functions that analyze test data usinng pandas and numpy. Additionally,
The stats are written into an analysis file and tables into an excel file (using excel_write module).
The "do_analysis" function at the end of this file pulls from the other modules to conduct a
comprehensive analysis of the input test data (statisics, tables, temporal plot, histograms). '''


from dataframe_building import *
from plotting_and_histograms import *
from limits_parser import *
from excel_write import *

import numpy as np
import csv
from subprocess import Popen


###### WRITING TABLES AND STATS TO EXCEL/TXT FILES ######
def current_stats(filenames, wb, ws, row_start, test_title, df, board, limits, temp):
    ''' mask => on/off status of boards (e.g. - '1100')
        df => dataframe
        limits => dictionary limits file to use for analysis
        temp => integer temp to analyze '''
    analysis_file = filenames[0]  ## filename for writing data analysis
    product = limits.product  ## product from limits file (e.g.- "P558 PV AUX")
    tolerance = TEMPERATURE_TOLERANCE  ## temperature tolerance
    vtol = VOLTAGE_TOLERANCE  ## voltage tolerance
    header = '==============================================='
    print('\n')
    bnums = get_bnums(df)  ## get boards present in mask dframe
    b_start = int(bnums[0][-1])  ## find lowest test station board number
    systems = [df.columns[i] for i in range(len(df.columns)) if re.search(REGEX_BNUMS(board), df.columns[i])]
    vsenses = [df.columns[i] for i in range(len(df.columns)) if re.search(REGEX_VSENSE(board), df.columns[i])]
    vsetpoint = 'VSetpoint ' + board
    temp_header = 'Amb Temp TC1 ' + board
    mode = board.upper()
    voltages = sorted(set(df[vsetpoint]))  ## find voltages setpoints used in mode
    print('BOARD MODE:', mode, '  TEMPERATURE:', str(temp)+'C')
    print('##########################################################')
    print('Board:', board, '  Detected test voltages: ', voltages)

    volt_dict = {}
    for voltage in voltages:
        volt_dict[voltage] = df.loc[(df[vsetpoint] == voltage) &
                            (df[temp_header] > (temp-tolerance)) &
                            (df[temp_header] < (temp+tolerance))]
    ## print title header at top of excel tables
    row_start = excel_write_title_header(row_start, wb, ws, len(systems)+2, filenames[-1])
    ## current/voltage/outage analysis for each voltage
    for voltage in voltages:
        ## set data to analyze
        dframe = volt_dict[voltage]
        ## set current limits
        LL, UL = limits.lim[temp][mode][voltage][0], limits.lim[temp][mode][voltage][1]
        ## create count lists
        count = []
        stat_data = [['TP:'],['MIN:'],['MAX:'],['AVG:'],['Count:'],['Out of Spec:']]
        ### input voltage check
        for vsense in vsenses:
            v_out_of_spec = dframe.loc[(dframe[vsense]<voltage-vtol) | (dframe[vsense]>voltage+vtol)]
            stat_data[0].append(vsense[:-3]) ## tp/system and strip board number
            stat_data[1].append(round(dframe[vsense].min(), 3)) ## min
            stat_data[2].append(round(dframe[vsense].max(), 3)) ## max
            stat_data[3].append(round(dframe[vsense].mean(), 3)) ## avg
            stat_data[4].append(len(dframe[vsense])) ## count (num scans)
            stat_data[5].append(len(v_out_of_spec)) ## out of spec
        ### current limits check
        for sys in systems:
            print('***', sys, 'Analyzing', len(dframe[sys]), 'current scans...', end='')
            out_of_spec = dframe.loc[(dframe[sys]<LL) | (dframe[sys]>UL)]
            count.append(len(out_of_spec))
            stat_data[0].append(sys[:-3]) ## tp/system and strip board number
            stat_data[1].append(round(dframe[sys].min(), 4)) ## min
            stat_data[2].append(round(dframe[sys].max(), 4)) ## max
            stat_data[3].append(round(dframe[sys].mean(), 4)) ## avg
            stat_data[4].append(len(dframe[sys])) ## count (num scans)
            stat_data[5].append(len(out_of_spec)) ## out of spec
            print(len(out_of_spec), 'out of spec')

        ### write current data analysis into analysis csv file
        with open(analysis_file, 'a') as f:
            writer = csv.writer(f, lineterminator='\n')
            writer.writerow(['==========']*13)
            writer.writerow([product, limits.boards_dict[board]+' only', str(board)+' only',
                             str(temp)+'C', str(voltage) + 'V', 'LL: ' + str(LL), 'UL: ' + str(UL)])
            for row in stat_data:
                writer.writerow(row)
            writer.writerow(['==>TOTAL: ', sum(count)])
            writer.writerow('')

        ## make "G" or "Out of Spec" current table data array
        table_data = stat_data[:3].copy()
        tbl_spec = stat_data[5][1:]
        tbl_chk = ['G' if (num==0) else 'Out of Spec' for num in tbl_spec]
        tbl_chk.insert(0, 'Check Data:')

        ### WRITE CURRENT TABLES INTO EXCEL FILE
        table_data.append(tbl_chk)
        row_start = excel_write_tbl_data(row_start, wb, ws, product, test_title, limits.boards_dict[board], str(temp), voltage, LL, UL, table_data)
    return row_start


def outage_stats(filenames, wb, ws, row_start, test_title, df, board, limits, temp):
    ''' Tesla M3 outage should always be 13.5 (no matter the on/off state or voltage sp). Only off when hard failure. '''
    ### basic info
    analysis_file = filenames[0]  ## filename for writing data analysis
    product = limits.product  ## product from limits file (e.g.- "P558 PV AUX")
    voltage = 'All Voltages'
    tolerance = TEMPERATURE_TOLERANCE  ##  temperature tolerance
    temp_header = 'Amb Temp TC1 ' + board
    dframe = df.loc[ (df[temp_header] > (temp-tolerance)) &
                       (df[temp_header] < (temp+tolerance)) ]
    ### set outage data
    outage_systems = [dframe.columns[i] for i in range(len(dframe.columns)) if re.search(REGEX_BNUMS('B6'), dframe.columns[i])]
    print(outage_systems)
    outage_LL, outage_UL = limits.outage['OFF'][0], limits.outage['OFF'][1]  ### coded to always use 'OFF' condition which is same as 'ON' (should always be 13.5V)
    outage_data = [['TP:'],['MIN:'],['MAX:'],['AVG:'],['Count:'],['Out of Spec:']]
    outage_count = []

    for sys in outage_systems:
        print('***', sys, 'Analyzing', len(dframe[sys]), 'outage scans...', end='')
        o_out_of_spec = dframe.loc[(dframe[sys]<outage_LL) | (dframe[sys]>outage_UL)]
        outage_count.append(len(o_out_of_spec))
        outage_data[0].append(sys[:-3]) ## tp/system and strip board number
        outage_data[1].append(round(dframe[sys].min(), 3)) ## min
        outage_data[2].append(round(dframe[sys].max(), 3)) ## max
        outage_data[3].append(round(dframe[sys].mean(), 3)) ## avg
        outage_data[4].append(len(dframe[sys])) ## count (num scans)
        outage_data[5].append(len(o_out_of_spec)) ## out of spec
        print(len(o_out_of_spec), 'out of spec')

    ## write outage data analysis into analysis csv
    with open(analysis_file, 'a') as f:
        writer = csv.writer(f, lineterminator='\n')
        if outage_UL == 1000:
            outage_UL = 'NA'
        writer.writerow([product, 'OUTAGE ('+limits.boards_dict[board]+' only)', 'OUTAGE ('+str(board)+' only)',
                         str(temp)+'C', str(voltage) + 'V', 'LL: ' + str(outage_LL), 'UL: ' + str(outage_UL)])
        for row in outage_data:
            writer.writerow(row)
        writer.writerow(['==>TOTAL: ', sum(outage_count)])
        writer.writerow('')

    ## make "G" or "Out of Spec" outage table data array
    outage_table_data = outage_data[:3].copy()
    outage_tbl_spec = outage_data[5][1:]
    outage_tbl_chk = ['G' if (num==0) else 'Out of Spec' for num in outage_tbl_spec]
    outage_tbl_chk.insert(0, 'Check Data:')

    ### WRITE OUTAGE TABLES INTO EXCEL FILE
    outage_table_data.append(outage_tbl_chk)
    outage_mode = 'OUTAGE'

    print('OUTAGE TABLE DATA:', outage_table_data)
    row_start = excel_write_title_header(row_start, wb, ws, len(outage_systems), filenames[-1])
    row_start = excel_write_tbl_data(row_start, wb, ws, product, test_title, outage_mode, str(temp), voltage, str(outage_LL), str(outage_UL), outage_table_data)
    return row_start

def write_full_module_stats(filenames, wb, ws, test_title, df, limits, temp):
    row_start = 0  ## where to start writing in excel tables file
    boards = get_bnums(df)  ## get boards present in mask dframe
    for board in boards:
        board_on_off = 'Board on/off ' + board
        if board == 'B6':  ## if board is outage
            # board_df = df.loc[(df[board_on_off] != -1)]  ## set dataframe to only when FC is ON
            board_df = df
            row = outage_stats(filenames, wb, ws, row_start, test_title, board_df, board, limits, temp)
            row_start = row + 4 ## buffer for different tables
        else:
            board_df = df.loc[(df[board_on_off] == 1)]  ## set dataframe to only when board is ON
            row = current_stats(filenames, wb, ws, row_start, test_title, board_df, board, limits, temp)
            row_start = row + 4  ## buffer for different tables


###### MAIN ANALYSIS FUNCTION -- CREATES TABLES, STATS, PLOTS, HISTOGRAMS ######
def do_analysis(filename, folder, b_nums, limits, stats, plots, hists, *temps):
    ''' Do user input analysis: stats/tbls, plotting, histograms possible
        (e.g. - type in 135 to see boards 1, 3, and 5) '''
    output_path = '!output//'
    filenames = [output_path + str(filename)+'-analysis.csv',
                 output_path + str(filename)+'-outofspec.csv', filename] ## leave filename last if altered!!!
    b_nums= str(b_nums)
    boards = sorted(['B'+num for num in b_nums])
    mdf, test_title = build_select_df(folder, *boards)

    ## make txt file with all boards
    mdf.to_csv(output_path + 'raw_data_all_boards.txt', header=mdf.columns, index=True, sep='\t', mode='a')

    ## user selected analysis
    if stats: ## stats/tables and essential plotting
        wb = create_excel_file(filename + ' - tables')
        for temp in temps:
            sheetname = str(temp) + 'C'
            ws = create_new_sheet(wb, sheetname)
            write_full_module_stats(filenames, wb, ws, test_title, mdf, limits, temp)
            highlight_workbook(wb, ws)
        wb.close()
    if (plots or hists):
        plt.ion()  ## interactive plotting mode
        if plots: ## essential voltage and current plots
            make_mplots(mdf, limits, filename)
        if hists: ## plot histograms if desired
            for temp in temps:
                histograms(mdf, limits, temp, filename)
        plt.show('hold') ## wait until all plots are built to show them
