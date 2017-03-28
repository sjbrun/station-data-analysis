#!/usr/bin/python3

''' This module contains functions that help build dataframes (data type created using "pandas")
from the selected test data text files. These dataframes  are passed on to other modules for analysis
(statistics, tables, plotting, histograms, etc.). The "dataframe" data type is lightweight and efficient;
it is extremely useful format for conducting this type of large data size analysis. '''


from regular_expressions_and_globals import *
from histograms import *
import itertools
import pandas as pd
import os
from datetime import datetime


DATE_PARSER = lambda x: pd.datetime.strptime(x, '%m/%d/%Y %I:%M:%S %p')  ## parsing function for datetime dataframes


class Sample(object):
    ''' This class may be useful... not sure yet '''
    def __init__(self, system, board):
        self.system = system
        self.board = board


class Board(object):
    ''' blah blah blah '''
    amb_temp = 'Amb Temp TC1'
    vsetpoint = 'VSetpoint'

    def __init__(self, test, board_number):
        self.test = test
        self.id = ''
        self.folder = test.folder
        self.files = []
        self.df = pd.DataFrame()
        self.systems = []
        self.thermocouples = []
        self.outage = False
        self.module = 'Not yet pulled from limits file'  # e.g. - 'DRL'
        self.samples = []
        
        self.__set_bnum(board_number)
        self.__set_outage()
        self.__build_dataframe()
        self.__delete_empty_columns()
        self.__scan_for_systems()
        self.__scan_for_voltage_senses()
        self.__scan_for_thermocouples()
        self.__create_samples()

    def __set_bnum(self, board_number):
        if type(board_number) == int:
            self.id = 'B'+str(board_number)
        elif type(board_number) == str:
            if ('B' in board_number) or ('b' in board_number):
                self.id = board_number.upper()
            else:
                self.id = 'B' + board_number

    def __set_outage(self):
        ''' True/False if board is Outage '''
        self.outage = '6' in self.id

    def __build_dataframe(self):
        ''' Builds all files in folder for board into a single dataframe 
        using the pandas module'''
        print('Building ' + self.id + ' dataframe...')
        for filename in os.listdir(self.folder):
            if bool(re.search(REGEX_BOARDFILE(self.id), filename)):
                try:
                    next_file_df = pd.read_csv( self.folder+'\\'+filename, parse_dates={'Date Time': [0,1]},
                                        date_parser=DATE_PARSER, index_col='Date Time', sep='\t',
                                        skipfooter=1, engine='python', usecols=range(22))
                except Exception:
                    print('The following error occurred while attempting to convert the ' \
                          'data files to pandas dataframes:\n\n')
                    raise
                self.files.append(filename)
                self.df = self.df.append(next_file_df)
        
        print('...complete.')
        
    def __delete_empty_columns(self):
        ''' Deletes emtpy columns in dataframe '''
        for col in self.df.columns.copy():
            if re.search('^TP[0-9]*:\s$', col):
                del self.df[col]
        temps = [self.df.columns[i] for i in range(len(self.df.columns)) if re.search(REGEX_TEMPS, self.df.columns[i])]
        for temp_col in temps.copy():  ## delete temperature columns with no readings
            if self.df[temp_col][0] == 'No Reading':
                del self.df[temp_col]

    def __scan_for_systems(self):
        ''' Scans data for all systems and gets rid of blank test positions '''
        self.systems = [self.df.columns[i] for i in range(len(self.df.columns)) if re.search(REGEX_SYSTEMS, self.df.columns[i])]

    def __scan_for_voltage_senses(self):
        ''' Scans for voltage sense columns '''
        self.voltage_senses = [self.df.columns[i] for i in range(len(self.df.columns)) if re.search(REGEX_VOLTAGE_SENSES, self.df.columns[i])]

    def __scan_for_thermocouples(self):
        ''' Scans for thermocouple columns '''
        self.thermocouples = [self.df.columns[i] for i in range(len(self.df.columns)) if re.search(REGEX_TEMPS, self.df.columns[i])]

    def __create_samples(self):
        ''' Creates a sample object for each system on the board '''
        for system in self.systems:
            self.samples.append(Sample(system, self))


class Mode(object):
    ''' This class may be useful, not sure yet '''

    amb_temp = 'Amb Temp TC1'
    vsetpoint = 'VSetpoint'

    def __init__(self, test, board_mode, df, voltages, *temps):
        self.test = test
        self.board_mode = board_mode
        self.mode_tag = board_mode.replace('B6', '')
        self.temps = temps
        self.voltages = voltages
        self.board_ids = re.findall('..', board_mode) # split string every 2 chars
        self.current_board_ids = copy_and_remove_b6_from(self.board_ids)
        self.systems = [' '.join([sys, self.mode_tag]) for sys in test.systems]
        self.hist_dict = {}  # temp -> voltage -> df of just currents at that temp/voltage combo
        self.multimode = False  # placeholder -> scans later to see if multimode or not
        self.mode_df = pd.DataFrame()
        
        self.__scan_for_multimode()
        self.__make_hist_dict()
        self.__populate_hist_dict(df)

    def __scan_for_multimode(self):
        if len(self.current_board_ids) > 1:
            self.multimode = True     

    def __make_hist_dict(self):
        empty_hist_dict = dict.fromkeys(self.voltages)
        for temp in self.temps:
            self.hist_dict[temp] = empty_hist_dict.copy()

    def __populate_hist_dict(self, df):    
        for temp in self.temps:
            for voltage in self.voltages:
                dframe = self.filter_temp_and_voltage(df, temp, voltage)
                self.mode_df = self.create_multimode_cols(dframe)
                dframe_for_hist = self.strip_index(self.mode_df)
                self.hist_dict[temp][voltage] = dframe_for_hist

    def filter_temp_and_voltage(self, df, temp, voltage):
        dframe = df.loc[(df[self.vsetpoint] == voltage) &
                        (df[self.amb_temp] > (temp-TEMPERATURE_TOLERANCE)) &
                        (df[self.amb_temp] < (temp+TEMPERATURE_TOLERANCE))]
        return dframe

    def create_multimode_cols(self, dframe):
        if self.multimode:  # if mode is a multimode (multiple current boards ON)
            for sys in self.test.systems: # for each system (without appended board/mode tag label)
                sys_col_label = sys + ' ' + self.mode_tag 
                dframe[sys_col_label] = 0.0  # create multimode col of float zeroes
                for b in self.current_board_ids: # add each ON current board
                    dframe[sys_col_label] = dframe[sys_col_label] + pd.to_numeric(dframe[sys+' '+b], downcast='float')
        return dframe

    def strip_index(self, dframe):
        hist_dframe = pd.melt(dframe, value_vars=self.systems, value_name='currents')
        hist_dframe = pd.to_numeric(hist_dframe['currents'], downcast='float')
        return hist_dframe


## helper
def copy_and_remove_b6_from(a_list):
    b_list = a_list.copy()
    try:
        b_list.remove('B6')  # remove outage
    except ValueError:
        pass  # do nothing
    return b_list    



class TestStation(object):
    ''' blah blah blah '''

    def __init__(self, boards, folder, *temps):
        self.folder = folder
        self.systems = []
        self.voltages = []
        self.temps = temps
        self.vsetpoint = 'VSetpoint'
        self.voltage_senses = []
        self.thermocouples = []
        self.on_off = [ON_OFF]
        self.boards = []
        self.board_ids = []
        self.b1 = 'Not Used'
        self.b2 = 'Not Used'
        self.b3 = 'Not Used'
        self.b4 = 'Not Used'       
        self.b5 = 'Not Used'
        self.b6 = 'Not Used'
        self.mdf = pd.DataFrame() # 'mother' dataframe holds all measured data
        self.mode_df_dict = {}  # holds mode_df for each data mask
        self.modes = []
        self.mode_stats = []

        self.__create_boards(boards)
        self.__set_on_boards()
        self.__set_board_ids()
        self.__set_systems()
        self.__set_voltage_senses()
        self.__set_thermocouples()
        self.__build_test_station_dataframe()
        self.__scan_for_vsetpoints()
        self.__make_df_dict()
        self.__make_mode_stats()

    def __create_boards(self, boards):
        ''' Creates board dataframes for each board passed into TestStation init '''
        boards = str(boards)  ## e.g. - boards: 123456 or 3456, etc
        for board in boards:
            if '1' in board:
                self.b1 = Board(self, board)
            elif '2' in board:
                self.b2 = Board(self, board)
            elif '3' in board:
                self.b3 = Board(self, board)
            elif '4' in board:
                self.b4 = Board(self, board)
            elif '5' in board:
                self.b5 = Board(self, board)
            elif '6' in board:
                self.b6 = Board(self, board)

    def __set_on_boards(self):
        ''' Appends all test boards that were used to boards list '''
        for board in [self.b1, self.b2, self.b3, self.b4, self.b5, self.b6]:
            if board != 'Not Used':
                self.boards.append(board)

    def __set_board_ids(self):
        for board in self.boards:
            self.board_ids.append(board.id)

    def __set_systems(self):
        ''' Sets the systems tested to the systems scanned on the first board '''
        self.systems = self.boards[0].systems

    def __set_voltage_senses(self):
        ''' Sets the voltage senses used to the voltage senses scanned on the first board '''
        self.voltage_senses = self.boards[0].voltage_senses

    def __set_thermocouples(self):
        ''' Sets the thermocouples used to the tcs scanned on the first board '''
        self.thermocouples = self.boards[0].thermocouples

    def __build_test_station_dataframe(self):
        ''' Builds a single test station "mother dataframe" (mdf) that includes
            all of the boards used for the test '''
        for board in self.boards:
            if self.mdf.empty:  ## if mdf is empty, assign mdf to first board dataframe 
                self.mdf = board.df.copy() 
            else:  ## append board df with board id suffix for matching columns
                self.mdf = self.mdf.join(board.df[self.on_off+self.voltage_senses+self.systems], rsuffix=' '+board.id)
        rename_columns(self.mdf, self.boards[0], self.on_off+self.voltage_senses+self.systems) ## rename columns of first df appended

    def __scan_for_vsetpoints(self):
        self.voltages = sorted(set(self.mdf[self.vsetpoint]))

    def __make_df_dict(self):
        ''' Outputs dictionary of ON time mask modes dataframes. This includes
            all boards in df (even off ones, outage included). '''
        masks = [''.join(seq) for seq in itertools.product('01', repeat=len(self.boards))]  ## list of all combinations on/off
        ## print('\t=> Possible board combinations: ', masks)
        for mask in masks:  ## retrieve only excited modes
            if '1' not in mask:
                continue
            mode = mask_to_mode(mask, self.board_ids)
            float_mask = [float(digit) for digit in mask]  ## float type to compare with df board on/off col
            data = self.mdf.copy() ## make copy of 'mother' dataframe
            ## for each specific mode (mask), join together all board dfs that are ON in mask
            i = 0
            for i in range(len(mask)):
                board, on_off_state = self.boards[i].id, float_mask[i]
                data = data.loc[(self.mdf[ON_OFF+' '+board] == on_off_state)]
                i += 1
            self.mode_df_dict[mode] = data  ## save mode data in dictionary with mask (mode) keys
            if self.mode_df_dict[mode].empty:
                del(self.mode_df_dict[mode])  ## delete data from dict if mode (mask) df is empty
        self.modes = list(self.mode_df_dict.keys())
        print('\n=> Board combos present: ', self.modes)

    def __make_mode_stats(self):
        for mode in self.modes:
            self.mode_stats.append(Mode(self, mode, self.mode_df_dict[mode], self.voltages, *self.temps))

    def print_board_numbers(self):
        ''' Prints the ON boards used in test station for test '''
        for board in self.boards:
            print(board.id)


### ------- Helper Functions ------- ###
def rename_columns(mdf, board, columns):
    ''' This is a helper function that adds the board number to the labels of the
    input columns. Used for creating 'mother' dataframe for TestStation object. '''
    for column_label in columns:
        mdf.rename(columns={column_label: column_label+' '+board.id}, inplace=True)
    return mdf

def mask_to_mode(mask, board_ids):
    mode = ''
    i = 0
    for binary_digit in mask:
        if int(binary_digit):
            mode += board_ids[i]
        i += 1
    return mode


### ----------------- TESTING ---------------- ###

FP = r"\\Chfile1\ecs_landrive\Automotive_Lighting\LED\P552 MCA Headlamp\P552 MCA Aux\ADVPR\PV Aux\TL A&B\Initial Tri Temp FT\-40C rerun\Raw Data"
test = TestStation(3456, FP, -40)
m = test.mode_stats[0]
v9 = m.hist_dict[-40][9.0]
make_mode_histograms(test)

