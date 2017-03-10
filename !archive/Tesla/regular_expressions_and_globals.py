#!/usr/bin/python3

''' This module contains useful regular expressions and tolerance global variables used
by some of the other modules. '''

import re

### TOLERANCE VARIABLES ###
TEMPERATURE_TOLERANCE = 5
VOLTAGE_TOLERANCE = 0.5

### MATPLOTLIB STYLES ###
GGBRUNO = "\\chfile1\ecs_landrive\Automotive_Lighting\LED\Test Engineering\Python Data Analysis\styles\ggbruno.mplstyle"

###### REGULAR EXPRESSIONS  ######
REGEX_SYSTEMS = '^TP[0-9]*:\s\S+'
REGEX_TEMPS = 'TC.*'

def REGEX_BOARDFILE(board):
    return '^\d{8}_\d{6}_.*_\d{2}_'+board+'.txt$'
def REGEX_BNUMS(bnum):
    return '^TP[0-9]*:\s\S+.*'+bnum.upper()+'$'
def REGEX_TEMPS_BNUMS(bnum):
    return 'TC.*'+bnum.upper()+'$'
def REGEX_VSENSE(bnum):
    return '^VSense\s[1-2]\s'+bnum.upper()+'$'
def REGEX_VSENSE1(bnum):
    return '^VSense\s1\s'+bnum.upper()+'$'
