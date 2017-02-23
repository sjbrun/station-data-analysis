#!/usr/bin/python3

''' This module uses "xlsxwriter" to create excel tables with conditional formatting
for out of spec currents/voltages and color modes as well. '''

import xlsxwriter

def create_excel_file(filename):
    # Create a workbook and add a worksheet.
    wb = xlsxwriter.Workbook('!output/' + filename + '.xlsx', {'nan_inf_to_errors': True})
    return wb

def create_new_sheet(wb, sheetname):
    ws = wb.add_worksheet(sheetname)
    return ws

def excel_write_tbl_data(row_start, workbook, worksheet, product, test_title, mode, temperature, voltage, LL, UL, data):
    # Create header and header formats
    temperature_string = str(temperature) + u'\N{DEGREE SIGN}' + 'C'
    voltage_string = ''.join([str(voltage), 'V'])
    voltage_lim_string = ' '.join([str(voltage)+u'\N{PLUS-MINUS SIGN}'+'0.5V'])
    limits_string = ''
    if 'outage' in mode.lower():
        limits_string = '    '.join(['Limits:  ', 'Vin '+ str(LL)+' to '+ str(UL)+'V'])
        voltage_string = str(voltage)  ## change back for TESLA (no 'V' at end because 'All Voltages')
    else:
        limits_string = '     '.join(['Limits:  ', 'Vin ' + voltage_lim_string,
                        'Iin '+str(LL)+' to '+ str(UL) + ' A'])
    mode_string = '  '.join(['Mode:   ', mode, temperature_string, voltage_string])
    color_dict = { 'REVERSE': '#FFFFCC', 'TURN': '#800080', 'STOP': '#FF4646',
                    'TAIL1': '#8B4513', 'TAIL2': '#FFA500', 'OUTAGE': '#C0C0C0',
                    'TAIL BS': '#8B4513', 'TAIL LG': '#FFA500'}

    # Write mode header into first row (row_start). Rows and columns are zero indexed.
    row, col = row_start, 0
    print('****************** THIS IS THE MODE ======> ', mode)
    if mode in color_dict:
        bg = color_dict[mode]
    else:
        bg = 'gray'
    h_format = workbook.add_format({'align':'center', 'border': True, 'bold': True,
                                    'font_color': 'black', 'bg_color': bg})
    worksheet.merge_range(row, col, row, len(data[0])-1, mode_string, h_format)

    # Write limits header into second row
    row = row_start + 1
    lim_format = workbook.add_format({'align':'center', 'border': True, 'bold': True,
                                      'font_color': 'black', 'bg_color': '#D3D3D3'})
    worksheet.merge_range(row, col, row, len(data[0])-1, limits_string, lim_format)

    # Starting from 3rd row, write in voltage/current data
    row = row_start + 2
    d_format = workbook.add_format({'align':'center', 'border': True, 'font_color': 'black'})
    for data_line in (data):
        col = 0
        worksheet.write_row(row, col, data_line, d_format)
        row += 1
    return row

def excel_write_title_header(row_start, workbook, worksheet, width, title_header):
    row, col = row_start, 0
    t_format = workbook.add_format({'align': 'center', 'border': True, 'bold': True, 'font_color': 'black'})
    worksheet.merge_range(row, col, row, width, 'Test:     ' + title_header, t_format)
    return row_start+1

def highlight_workbook(workbook, worksheet):
    out_format = workbook.add_format({'bg_color': 'yellow', 'font_color': 'red'})
    worksheet.conditional_format('A1:O600', {'type': 'text', 'criteria': 'containing', 'value': 'Out of Spec', 'format': out_format})


# def get_col_widths(dataframe):
#     # First we find the maximum length of the index column
#     idx_max = max([len(str(s)) for s in dataframe.index.values] + [len(str(dataframe.index.name))])
#     # Then, we concatenate this to the max of the lengths of column name and its values for each column, left to right
#     return [idx_max] + [max([len(str(s)) for s in dataframe[col].values] + [len(col)]) for col in dataframe.columns]

# for i, width in enumerate(get_col_widths(metrics)):
#     worksheet.set_column(i, i, width)
