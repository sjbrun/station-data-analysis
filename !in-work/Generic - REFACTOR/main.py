from stats_and_analysis import *


###### MAIN ANALYSIS FUNCTION -- CREATES TABLES, STATS, PLOTS, HISTOGRAMS ######
def do_analysis(filename_and_title, folder, b_nums, limits, stats, plots, hists, *temps):
    ''' Do user input analysis: stats/tbls, plotting, histograms possible
        (e.g. - type in 135 to see boards 1, 3, and 5 '''
    boards, mdf, test_title, df_dict = setup_data(b_nums, folder)  # boards, dataframe, title, modedict
    filenames = setup_files(filename_and_title, folder, mdf) # analysis, outofspec, filename
    
    ## user-selected analysis
    outage_bool = False
    if 'B6' in boards:
        outage_bool = True
    if stats: ## stats/tables and essential plotting
        write_analysis_files(filenames, test_title, df_dict, limits, outage_bool, temps)
    if (plots or hists):
        plt.ion()  ## interactive plotting mode
        if plots: ## plot temporal voltages and currents if desired
            make_mplots(mdf, limits, filename_and_title)
        if hists: ## plot histograms if desired
            plot_histograms(filename_and_title, df_dict, limits, outage_bool, temps)
        print('\nAll analysis complete.')
        plt.show('hold') ## wait until all plots are built to show them

def setup_files(filename_and_title, folder, mdf):
    output_path = '!output//'
    filenames = [output_path + str(filename_and_title) +'-analysis.csv',
                 output_path + str(filename_and_title) +'-outofspec.txt',
                 filename_and_title]
    mdf.to_csv(output_path + 'raw_data_all_boards.txt', 
           header=mdf.columns, index=True, sep='\t', mode='a')
    return filenames

def setup_data(b_nums, folder):
    boards = sorted(['B'+num for num in str(b_nums)])
    mdf, test_title = build_select_df(folder, *boards)
    df_dict = make_modes(mdf)
    return boards, mdf, test_title, df_dict

def write_analysis_files(filenames, test_title, df_dict, limits, outage_bool, temps):
    print('Starting statistical analysis...\n')
    wb = create_excel_file(filenames[-1] + ' - tables')
    for temp in temps:
        sheetname = str(temp) + 'C'
        ws = create_new_sheet(wb, sheetname)
        write_full_module_stats(filenames, wb, ws, test_title, df_dict, limits, outage_bool, temp)
        highlight_workbook(wb, ws)
    wb.close()
    print('\n\n====>Statistical analysis complete\n')