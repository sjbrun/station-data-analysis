#!/usr/bin/python3

''' This module contains functions that analyze test data using pandas and numpy. Additionally,
The stats are written into an analysis file and formatted as tables in an excel file (using
excel_write module). The "do_analysis" function at the end of this file pulls from the other
modules to conduct a comprehensive analysis of the input test data (statisics, tables, temporal
plot, histograms). '''


from dataframe_building import *
from plotting_and_histograms import *
from limits_parser import *
from excel_write import *

import numpy as np
import csv
from subprocess import Popen



def parse_data_into_voltages(df, board, voltages):
    volt_dict = {}
    for voltage in voltages:
        volt_dict[voltage] = df.loc[(df[board.vsetpoint] == voltage) &
                            (df[board.amb_temp] > (temp-TEMPERATURE_TOLERANCE)) &
                            (df[board.amb_temp] < (temp+TEMPERATURE_TOLERANCE))]
    return volt_dict


def check_if_empty(dframe):
    if dframe.empty:
        seq = [str(temp)+u'\N{DEGREE SIGN}C', str(voltage)+'V', str(mode)+'. ']
        msg = '\nHung up at ' + ' '.join(seq) + \
              'There is no data for the selected temperature.'
        raise Exception(msg)


###### WRITING TABLES AND STATS TO EXCEL/TXT FILES ######
def write_single_stats(test_station, df, board, filenames, limits, wb, ws, row_start, temp):
    ''' df: dataframe from mode dictionary (only input board is ON)
        board: the test station board used to test the module
        limits: dictionary limits file to use for analysis
        temp: integer temperature to analyze '''
    analysis_file = filenames[0]  ## filename for writing data analysis
    test_title = filenames[-1]  ## test name for files, plots, etc.
    product = limits.product  ## product from limits file (e.g.- "P558 PV AUX")
    voltages = sorted(set(df[board.vsetpoint]))  ## find voltages setpoints used in mode
    print('BOARD MODE:', mode, '  TEMPERATURE:', str(temp)+'C')
    ## check if outage present in selected dataframes (e.g.- 3456)
    outage_present = False
    if 'B6' in bnums:  ## if outage is included in dataframe
        outage_present = True
        outage_systems = [df.columns[i] for i in range(len(df.columns)) if re.search(REGEX_BNUMS('B6'), df.columns[i])]
    print('##########################################################')
    print('Mask:', mask, '  Detected test voltages: ', voltages)
    
    ## parse dataframe data into voltage dictionary 
    volt_dict = parse_data_into_voltages(df, board, voltages)

    ## print title header at top of excel tables
    row_start = excel_write_title_header(row_start, wb, ws, len(systems)+2, filenames[-1])
    ## current/voltage/outage analysis for each voltage
    for voltage in voltages:
        dframe = volt_dict[voltage]  ## set data to analyze
        check_if_empty(dframe)  ## check if any data in df
        LL, UL = limits.lim[temp][mode][voltage][0], limits.lim[temp][mode][voltage][1]  ## set current limits
        
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
        mother_out_of_spec = pd.DataFrame()
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

            ## add to out of spec file if not empty
            if not out_of_spec.empty:
                if mother_out_of_spec.empty:
                    mother_out_of_spec = out_of_spec
                else:
                    pd.merge(mother_out_of_spec, out_of_spec)
        

        ## append to out of spec text file
        with open('!output//out_of_spec.txt', 'a+') as out_file:
            out_file.write('\t'.join(['\n' + str(temp) + u'\N{DEGREE SIGN}C',
                            str(limits.boards_dict[board]) + ' only',
                            str(voltage) + 'V', '\n']))
        mother_out_of_spec.to_csv('!output//out_of_spec.txt',
                                  header=mother_out_of_spec.columns,
                                  index=True, sep='\t', mode='a')

       


        ### write current data analysis into analysis csv file
        with open(analysis_file, 'a') as f:
            writer = csv.writer(f, lineterminator='\n')
            writer.writerow(['==========']*13)
            writer.writerow([product, limits.boards_dict[board]+' only', str(board)+' only', str(temp)+'C', str(voltage) + 'V', 'LL: ' + str(LL), 'UL: ' + str(UL)])
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

        ### outage check and write (if present)
        if outage_present:
            ## set outage limits
            if board == limits.outage_link:  ## outage is ON
                outage_LL = limits.outage['ON'][voltage][0]
                outage_UL = limits.outage['ON'][voltage][1]
                if outage_UL == 'NA':
                    outage_UL = 1000
            else: ## outage is OFF
                outage_LL = limits.outage['OFF'][0]
                outage_UL = limits.outage['OFF'][1]
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
                writer.writerow([product, 'OUTAGE ('+limits.boards_dict[board]+' only)', 'OUTAGE ('+str(board)+' only)', str(temp)+'C', str(voltage) + 'V', 'LL: ' + str(outage_LL), 'UL: ' + str(outage_UL)])
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
            for e in outage_table_data:
                for i in range(2):
                    e.insert(1, ' ')
            outage_mode = 'OUTAGE ('+limits.boards_dict[board]+' only)'
            row_start = excel_write_tbl_data(row_start, wb, ws, product, test_title, outage_mode, str(temp), voltage, str(outage_LL), str(outage_UL), outage_table_data)
    return row_start

def replace_board_with_line(label, board_dict):
    label_copy = label
    for board in board_dict:
        if board in label:
            label_copy = label.replace(board, board_dict[board])
            break
    return label_copy

def line_to_analysis_file(analysis_file, limits, boards_wo6, mm_data, product, real_mode, temp, voltage, MMLL, MMUL):
    ## write in multimode single line analysis into ANALYSIS file
    with open(analysis_file, 'a') as f:
        writer = csv.writer(f, lineterminator='\n')
        for board in boards_wo6:
            real_line = limits.boards_dict[board]
            writer.writerow([product, str(real_mode)+' ('+str(real_line)+')', str(temp)+'C', str(voltage) + 'V', 'MMLL: ' + str(MMLL), 'MMUL: ' + str(MMUL)])
            for row in mm_data[board]:
                writer.writerow(row)
            writer.writerow('')

def analyze_multi_mode_single_line(analysis_file, dframe, limits, boards_wo6, systems_only, product, real_mode, temp, voltage):
    ## MULTIMODE SINGLE LINE LIMIT ANALYSIS
    if limits.mm_lims != ('', ''):  ## if multimode single line limits are not empty
        ## analyze single current lines that are in multimode
        MMLL, MMUL = limits.mm_lims[0], limits.mm_lims[1]
        mm_data = {}
        for board in boards_wo6:
            for sys in systems_only:
                mm_data[board] = [['TP:'],['MIN:'],['MAX:'],['AVG:'],['Count:'],['Out of Spec:']]
        for board in boards_wo6:
            for sys in systems_only:
                tpos = sys + board
                mm_out_of_spec = dframe.loc[(dframe[tpos]<MMLL) | (dframe[tpos]>MMUL)]
                mm_data[board][0].append(sys) ## system
                mm_data[board][1].append(round(dframe[tpos].min(), 4)) ## min
                mm_data[board][2].append(round(dframe[tpos].max(), 4)) ## max
                mm_data[board][3].append(round(dframe[tpos].mean(), 4)) ## avg
                mm_data[board][4].append(len(dframe[tpos])) ## count (num scans)
                mm_data[board][5].append(len(mm_out_of_spec)) ## out of spec
    line_to_analysis_file(analysis_file, limits, boards_wo6, mm_data, product, real_mode, temp, voltage, MMLL, MMUL)


def write_multi_stats(filenames, wb, ws, row_start, test_title, data_dict, mask, limits, outage, temp):
    ''' Creates multimode current data from data_dict and mask and
        analyzes/writes input voltage, current and outage data to csv.
        Inputs:
            data_dict => dictionary of masked dataframes
            mask => on/off status of boards (e.g. - '11000')
            limits => dictionary limits file to use for analysis
            temp => integer temp to analyze '''
    analysis_file = filenames[0]  ## filename for writing data analysis
    product = limits.product  ## product name pulled from limits dict
    tolerance = TEMPERATURE_TOLERANCE  ## temperature tolerance
    vtol = VOLTAGE_TOLERANCE  ## voltage tolerance
    header = '==========='
    print('\n')
    df = data_dict[mask]  ## get appropriate dataframe (correct mode)
    bnums = get_bnums(df)  ## get boards present in mask dframe
    b_start = int(bnums[0][-1])  ## find lowest test station board number
    on_off_dict = dict(zip(bnums, mask))  ## keys=>boards, values=>on/off
    boards = [board for board in bnums if on_off_dict[board]=='1']  ## only ON boards
    boards_wo6 = [board for board in boards if (board != 'B6')]  ## on_boards that are not outage
    bmode = ''.join(str(b) for b in sorted(boards) if b != 'B6')  ## string board combo
    print('BOARD MODE:', bmode, '  TEMPERATURE:', str(temp)+'C')
    systems_only = [df.columns[i][:-2] for i in range(len(df.columns)) if re.search(REGEX_BNUMS(boards[0]), df.columns[i])]
    systems_bmode = [sys+bmode for sys in systems_only]
    vsenses = [df.columns[i][:-2] for i in range(len(df.columns)) if re.search(REGEX_VSENSE(boards[0]), df.columns[i])]
    vsenses_all = []
    non_outage_boards = [board for board in boards if board != 'B6']
    vsenses_all += [ (vsense+board) for board in non_outage_boards for vsense in vsenses ]
    vsetpoint = 'VSetpoint ' + boards[0]
    temp_header = 'Amb Temp TC1 ' + boards[0]  ## need this to access temperature in df
    mode = bmode.upper()

    ## create multimode current columns -- NEED FOR MULTIMODE ANALYSIS
    for sys in systems_only:
        df[sys+bmode] = 0
        for b in boards:
            if b != 'B6':
                df[sys+bmode] = df[sys+bmode] + df[sys+b]
    voltages = sorted(set(df[vsetpoint]))  ## find voltages setpoints used in mode
    if outage:  ## if outage is included in dataframe
        outage_systems = [df.columns[i] for i in range(len(df.columns)) if re.search(REGEX_BNUMS('B6'), df.columns[i])]
    print('##########################################################')
    print('Mask:', mask, '  Detected test voltages:', voltages)
    volt_dict = {}

    ## divide df into subdfs of different voltages
    for voltage in voltages:
        volt_dict[voltage] = df.loc[(df[vsetpoint] == voltage) &
                            (df[temp_header] > (temp-tolerance)) &
                            (df[temp_header] < (temp+tolerance))]
    ## print title header at top of excel tables
    row_start = excel_write_title_header(row_start, wb, ws, len(systems_only)+len(boards_wo6)*2, filenames[-1])

    ## get real product mode (not just boards mode)
    real_mode = ''
    for board in boards_wo6:
        real_mode += limits.boards_dict[board]

    ## current/voltage/outage analysis for each voltage
    for voltage in voltages:
        dframe = volt_dict[voltage]
        ## check if any data in df
        if dframe.empty:
            print('\n')
            seq = [str(temp)+u'\N{DEGREE SIGN}C', str(voltage)+'V', str(real_mode)+'. ']
            msg = '\nHung up at ' + ' '.join(seq) + \
                  'There is no data for the selected temperature.'
            raise Exception(msg)
        ## set limits and empty stat arrays
        LL, UL = limits.lim[temp][mode][voltage][0], limits.lim[temp][mode][voltage][1]
        count = []
        stat_data = [['TP:'],['MIN:'],['MAX:'],['AVG:'],['Count:'],['Out of Spec:']]

        ### input voltage check
        for vsense in vsenses_all:
            v_out_of_spec = dframe.loc[(dframe[vsense]<voltage-vtol) | (dframe[vsense]>voltage+vtol)]
            stat_data[0].append(replace_board_with_line(vsense, limits.boards_dict)) ## tp/system and replace board number w/ line
            stat_data[1].append(round(dframe[vsense].min(), 3)) ## min
            stat_data[2].append(round(dframe[vsense].max(), 3)) ## max
            stat_data[3].append(round(dframe[vsense].mean(), 3)) ## avg
            stat_data[4].append(len(dframe[vsense])) ## count (num scans)
            stat_data[5].append(len(v_out_of_spec)) ## out of spec

        ### current limits check
        mother_out_of_spec = pd.DataFrame()  ## empty df for out of spec currents
        for sys in systems_bmode:
            print('***', sys, 'Analyzing', len(dframe[sys]), 'current scans...', end='')
            out_of_spec = dframe.loc[(dframe[sys]<LL) | (dframe[sys]>UL)]
            count.append(len(out_of_spec))
            stat_data[0].append(systems_only[systems_bmode.index(sys)]) ## tp/system
            stat_data[1].append(round(dframe[sys].min(), 4)) ## min
            stat_data[2].append(round(dframe[sys].max(), 4)) ## max
            stat_data[3].append(round(dframe[sys].mean(), 4)) ## avg
            stat_data[4].append(len(dframe[sys])) ## count (num scans)
            stat_data[5].append(len(out_of_spec)) ## out of spec
            print(len(out_of_spec), 'out of spec')
            ## add to out of spec file if not empty
            if not out_of_spec.empty:
                if mother_out_of_spec.empty:
                    mother_out_of_spec = out_of_spec
                else:
                    pd.merge(mother_out_of_spec, out_of_spec)

        ## append to out of spec text file
        with open('!output//out_of_spec.txt', 'a+') as out_file:
            out_file.write('\t'.join(['\n' + str(temp) + u'\N{DEGREE SIGN}C',
                            str(real_mode),
                            str(voltage) + 'V', '\n']))
        mother_out_of_spec.to_csv('!output//out_of_spec.txt',
                                  header=mother_out_of_spec.columns,
                                  index=True, sep='\t', mode='a')

        ## write current data into ANALYSIS file
        with open(analysis_file, 'a') as f:
            writer = csv.writer(f, lineterminator='\n')
            writer.writerow(['==========']*13)
            writer.writerow([product, real_mode, str(temp)+'C', str(voltage) + 'V', 'LL: ' + str(LL), 'UL: ' + str(UL)])
            for row in stat_data:
                writer.writerow(row)
            writer.writerow(['==>TOTAL: ', sum(count)])
            writer.writerow('')

        ## make "G" or "Out of Spec" table data array
        table_data = stat_data[:3].copy()
        tbl_spec = stat_data[5][1:]
        tbl_chk = ['G' if (num==0) else 'Out of Spec' for num in tbl_spec]
        tbl_chk.insert(0, 'Check Data:')

        ### WRITE CURRENT TABLES INTO EXCEL FILE
        table_data.append(tbl_chk)
        row_start = excel_write_tbl_data(row_start, wb, ws, product, test_title, real_mode, str(temp), voltage, LL, UL, table_data)

        ## MULTIMODE SINGLE LINE LIMIT ANALYSIS (if present)
        analyze_multi_mode_single_line(analysis_file, dframe, limits, boards_wo6, systems_only, product, real_mode, temp, voltage)

        ### OUTAGE check and write (if present)
        if outage:
            ## set outage limits
            if limits.outage_link in boards:  ## outage is ON
                outage_LL = limits.outage['ON'][voltage][0]
                outage_UL = limits.outage['ON'][voltage][1]
                if outage_UL == 'NA':
                    outage_UL = 1000
            else: ## outage is OFF
                outage_LL = limits.outage['OFF'][0]
                outage_UL = limits.outage['OFF'][1]
            ## hold outage stats data in lists
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

            ### write outage data into ANALYSIS csv
            with open(analysis_file, 'a') as f:
                writer = csv.writer(f, lineterminator='\n')
                if outage_UL == 1000:
                    outage_UL = 'NA'
                writer.writerow([product, 'OUTAGE ('+real_mode+')', str(temp)+'C', str(voltage) + 'V', 'LL: ' + str(outage_LL), 'UL: ' + str(outage_UL)])
                for row in outage_data:
                    writer.writerow(row)
                writer.writerow('')

            ## make "G" or "Out of Spec" table data array
            outage_table_data = outage_data[:3].copy()
            outage_tbl_spec = outage_data[5][1:]
            outage_tbl_chk = ['G' if (num==0) else 'Out of Spec' for num in outage_tbl_spec]
            outage_tbl_chk.insert(0, 'Check Data:')

            ### WRITE OUTAGE TABLES INTO EXCEL FILE
            outage_table_data.append(outage_tbl_chk)
            times = len(boards_wo6)*2
            for e in outage_table_data:
                for i in range(times):
                    e.insert(1, ' ')
            outage_mode = 'OUTAGE ('+real_mode+')'
            row_start = excel_write_tbl_data(row_start, wb, ws, product, test_title, outage_mode, str(temp), voltage, str(outage_LL), str(outage_UL), outage_table_data)
    return row_start


def write_full_module_stats(filenames, wb, ws, test_title, data_dict, limits, outage, temp):
    ''' Note differences in parameters passed depending on single or
        multi stats function call '''
    row_start = 0  ## where to start writing in excel tables file
    for mask in sort_masks(list(data_dict.keys()), outage):
        if outage:  ## outage ON
            if (mask.count('1') == 1) or (outage and (mask.count('1') == 2) and mask[-1] == '1'):
                row = write_single_stats(filenames, wb, ws, row_start, test_title, data_dict[mask], mask, limits, outage, temp)
            elif (mask.count('1') > 2) or (outage and (mask.count('1') == 2) and mask[-1] == '0'):
                row = write_multi_stats(filenames, wb, ws, row_start, test_title, data_dict, mask, limits, outage, temp)
        else:  ## outage OFF
            if (mask.count('1') == 1):
                row = write_single_stats(filenames, wb, ws, row_start, test_title, data_dict[mask], mask, limits, outage, temp)
            elif (mask.count('1') > 1):
                row = write_multi_stats(filenames, wb, ws, row_start, test_title, data_dict, mask, limits, outage, temp)
        row_start = row + 4  ## buffer for different tables



