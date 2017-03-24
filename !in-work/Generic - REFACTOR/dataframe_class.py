#!/usr/bin/python3

''' This module contains functions that help build dataframes (data type created using "pandas")
from the selected test data text files. These dataframes  are passed on to other modules for analysis
(statistics, tables, plotting, histograms, etc.). The "dataframe" data type is lightweight and efficient;
it is extremely useful format for conducting this type of large data size analysis. '''


from regular_expressions_and_globals import *
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

    def __init__(self, board_number, folder):
        self.id = ''
        self.folder = folder
        self.files = []
        self.df = pd.DataFrame()
        self.systems = []
        self.thermocouples = []
        self.outage = False
        self.module = 'Not yet pulled from limits file'  # e.g. - 'DRL'
        # self.samples = []
        
        self.__set_bnum(board_number)
        self.__set_outage()
        self.__build_dataframe()
        self.__delete_empty_columns()
        self.__scan_for_systems()
        self.__scan_for_voltage_senses()
        self.__scan_for_thermocouples()
        # self.__create_samples()

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
                    next_file_df = pd.read_csv(self.folder+'\\'+filename, parse_dates={'Date Time': [0,1]},
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
            self.samples.append(Sample(system, self.id))


class ModeStat(object):
    ''' This class may be useful, not sure yet '''
    def __init__(self, mode, df, voltages):
        self.mode = mode
        self.voltages = voltages


class TestStation(object):
    ''' blah blah blah '''

    def __init__(self, boards, folder):
        self.folder = folder
        self.systems = []
        self.voltages = []
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
        self.mdf = pd.DataFrame()
        self.mode_df_dict = {}  ## holds mode_df for each data mask

        self.__create_boards(boards)
        self.__set_on_boards()
        self.__set_board_ids()
        self.__set_systems()
        self.__set_voltage_senses()
        self.__set_thermocouples()
        self.__build_test_station_dataframe()
        self.__scan_for_vsetpoints()
        self.__make_modes()

    def __create_boards(self, boards):
        ''' Creates board dataframes for each board passed into TestStation init '''
        boards = str(boards)  ## e.g. - boards: 123456 or 3456, etc
        for board in boards:
            if '1' in board:
                self.b1 = Board(board, self.folder)
            elif '2' in board:
                self.b2 = Board(board, self.folder)
            elif '3' in board:
                self.b3 = Board(board, self.folder)
            elif '4' in board:
                self.b4 = Board(board, self.folder)
            elif '5' in board:
                self.b5 = Board(board, self.folder)
            elif '6' in board:
                self.b6 = Board(board, self.folder)

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

    def __make_modes(self):
        ''' Outputs dictionary of ON time mask modes dataframes. This includes
            all boards in df (even off ones, outage included). '''
        masks = [''.join(seq) for seq in itertools.product('01', repeat=len(self.boards))]  ## list of all combinations on/off
        print('\t=> Possible board combinations: ', masks)
        
        for mask in masks:  ## retrieve only excited modes
            float_mask = [float(digit) for digit in mask]  ## float type to compare with df board on/off col
            data = self.mdf.copy()
            ## for each specific mode (mask), join together all board dfs that are ON in mask
            i = 0
            for i in range(len(mask)):
                board, on_off_state = self.boards[i].id, float_mask[i]
                data = data.loc[(self.mdf[ON_OFF+' '+board] == on_off_state)]
                i += 1
            self.mode_df_dict[mask] = data  ## save mode data in dictionary with mask (mode) keys
            if self.mode_df_dict[mask].empty:
                del(self.mode_df_dict[mask])  ## delete data from dict if mode (mask) df is empty
        print('\t=> Board combos actually present: ', sorted(self.mode_df_dict.keys()))

    def print_board_numbers(self):
        ''' Prints the ON boards used in test station for test '''
        for board in self.boards:
            print(board.id)


### helper function rename columns
def rename_columns(mdf, board, columns):
    for column_label in columns:
        mdf.rename(columns={column_label: column_label+' '+board.id}, inplace=True)
    return mdf



FP = r"\\Chfile1\ecs_landrive\Automotive_Lighting\LED\P552 MCA Headlamp\P552 MCA Aux\ADVPR\PV Aux\TL A&B\Initial Tri Temp FT\-40C rerun\Raw Data"
test = TestStation(3456, FP)


