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


###### LOADING AND ADJUSTING TXT FILES FOR DATAFRAME BUILDS ######
def alter_file(filename):
    ''' This function changes the first line break to include a tab just before it '''
    with open(filename, "r+") as f:
        lines = f.readlines()
        if '\t\n' not in lines[0]:
            lines[0] = lines[0].replace('\n', '\t\n')
            f.seek(0)
            for line in lines:
                f.write(line)
            f.truncate()

parse = lambda x: pd.datetime.strptime(x, '%m/%d/%Y %I:%M:%S %p')  ## parsing function for datetime dataframes

###### BUILDING BOARDS, MODES AS DATAFRAMES ######
### =>TODO: logic to prevent exit/hang-up if raw data csv files are empty (headers only)
def build_dataframe(board, folder, rename=False):
    ''' Builds dataframe for specified board in specified folder '''
    print('Building '+board+' dataframe...', end='')
    df = pd.DataFrame()
    for filename in os.listdir(folder):
        if bool(re.search(REGEX_BOARDFILE(board), filename)):
            # alter_file(folder+'\\'+filename)
            new_df = pd.read_csv(folder+'\\'+filename, parse_dates={'Date Time': [0,1]}, date_parser=parse,
                                 index_col='Date Time', sep='\t', skipfooter=1, engine='python',
                                 usecols=range(22))
            df = df.append(new_df)
    for col in df.columns.copy():
        if re.search('^TP[0-9]*:\s$', col):
            del df[col]
    temps = [df.columns[i] for i in range(len(df.columns)) if re.search(REGEX_TEMPS, df.columns[i])]
    for temp_col in temps:  ## delete temperature columns with no readings
        if df[temp_col][0] == 'No Reading':
            del df[temp_col]
    if rename:  ## (if input true) append board num to each column
        df.columns = map(lambda x:x+' '+board, df.columns)
    try:
        df = df.replace(['OFF','No Reading'], [0,0])
        df = df.astype(float)
    except TypeError as e:
        print(e)
    print('complete.')
    return df

def build_select_df(folder, *boards):
    ''' Builds dataframes for each specified board and returns
        a single dataframe made by joining selected board dfs '''
    dataframes = []
    first_filepath = folder + '\\' + os.listdir(folder)[0] ## pull test title from first file
    with open(first_filepath) as f:
        name_line = f.readlines()[3]
        if 'Test Name' in name_line:
            #title = re.match(r'^Test Name: (.*)\.', name_line).group(0)
            title = re.findall(r'^Test Name:\s(.*)\.', name_line)[0]
        else:
            title = ''
    for board in boards:
        board = board.upper()
        df = build_dataframe(board, folder, True)
        dataframes.append(df)
    sdf = dataframes[0].join(dataframes[1:])
    return sdf, title

def mother_dataframe(folder):
    ''' Builds dataframes for each specified board and returns
        a "mother" dataframe made by joining all board dfs '''
    boards = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6']
    dataframes = []
    for board in boards:
        df = build_dataframe(board, folder, True)
        dataframes.append(df)
    mdf = dataframes[0].join(dataframes[1:])
    return mdf

def join_dfs(*dataframes):
    for df in dataframes:
        jdf = dataframes[0].join(dataframes[1:])
    return jdf

def add_dfs(df1, df2, m1, m2, only_on = False):
    mode = '_'+m1+m2
    temps = [df1.columns[i] for i in range(len(df1.columns)) if ('TC' in df1.columns[i])]
    volts = [df1.columns[i] for i in range(len(df1.columns)) if re.search('^VSense', df1.columns[i])]
    b_on_off = [df1.columns[i] for i in range(len(df1.columns)) if re.search('^Board', df1.columns[i])]
    systems = [df1.columns[i] for i in range(len(df1.columns)) if re.search(REGEX_SYSTEMS, df1.columns[i])]

    combined = pd.DataFrame()
    for t in temps:
        combined[t] = df1[t]
    combined['VSetpoint'] = df1['VSetpoint']
    for v in volts:  ## mode1 voltages
        combined[v+' '+m1] = df1[v]
    for v in volts:  ## mode2 voltages
        combined[v+' '+m2] = df2[v]
    combined['Board on/off '+m1] = df1['Board on/off']
    combined['Board on/off '+m2] = df2['Board on/off']
    if only_on: ## if you only want scans where both boards are powered
        combined2 = combined.ix[(combined['Board on/off '+m1] == 1) & (combined['Board on/off '+m2] == 1)]
        combined = combined2
    for sys in systems:
        combined[sys] = df1[sys]+df2[sys]
    combined = combined.astype(float)
    return combined

def make_modes(df):
    ''' Outputs dictionary of ON time mask modes dataframes. This includes
        all boards in df (even off ones, outage included). '''
    print('Creating dictionary of modes dataframes...')
    boards_present = []
    for board in ['B1','B2','B3','B4','B5','B6']:
        if any(board in col for col in df.columns):
            boards_present.append(board)
    col = 'Board on/off '  # whitespace char is there on purpose
    masks = [''.join(seq) for seq in itertools.product('01', repeat=len(boards_present))]  ## list of all combinations on/off
    print("\t=> Possible board combinations: ", masks)
    data_dict = {}  ## holds df for each data mask
    for mask in masks:  ## retrieve only excited modes
        float_mask = [float(digit) for digit in mask]  ## float type to compare with df board on/off col
        data = df.copy()
        ## for each specific mode (mask), join together all board df that are ON in mask
        i = 0
        for i in range(len(mask)):
            board, on_off_state = boards_present[i], float_mask[i]
            data = data.loc[(df[col+board] == on_off_state)]
            i += 1
        data_dict[mask] = data  ## save mode data in dictionary with mask (mode) keys
        if data_dict[mask].empty:
            del(data_dict[mask])  ## delete data from dict if mode (mask) df is empty
    print("\t=> Board combos actually present: ", sorted(data_dict.keys()))
    return data_dict

def create_modes(folder, b_nums):
    ''' Builds dfs and makes all modes. Outputs masked df_dict.
        b_nums = enter desired boards (e.g. - type in 135 to see boards 1, 3, and 5 '''
    b_nums= str(b_nums)
    boards = sorted(['B'+num for num in b_nums])
    mdf = build_select_df(folder, *boards)
    return make_modes(mdf)

def get_bnum(df):
    ''' Finds board of input dataframe '''
    for board in ['B1','B2','B3','B4','B5','B6']:
        if any(board in col for col in df.columns):
            return board
    return None

def get_bnums(mdf):
    ''' Finds boards included in input multi-dataframe '''
    boards_present = []
    for board in ['B1','B2','B3','B4','B5','B6']:
        if any(board in col for col in mdf.columns):
            boards_present.append(board)
    return boards_present
