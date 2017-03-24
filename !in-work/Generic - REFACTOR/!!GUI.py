#!/usr/bin/python3

''' This is the GUI code for the test analysis program. An interface is created with buttons
 and text fields for the user to input the test data to analyze and the type of analysis. Other
 modules are accessed to carry out the analysis, primarily the main "do_analysis" function from
 'stats_and_analysis' module. '''


############ EVENT AND BINDS ############
### http://www.python-course.eu/tkinter_events_binds.php
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from main import *

global bg_color ## background color for frame and widgets
global bg_button ## background color for button widgets
global bg_hover ## background color for button widgets when cursor is hovering over
bg_color = "light blue"
bg_button = "#e9e9e9"
bg_hover = "#d3d3d3"

class DataAnalysis(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        self.master = master
        master.title("Data Analysis")

        ### FONT PARAMETERS
        label_font = "Arial 11 bold"
        option_font = "Arial 10"
        big_btn_font = "Arial 10 bold"

        ### OPEN DATA FOLDER DIALOG -- select folder path for data analysis
        self.folderpath = StringVar()
        self.path_button = Button(text='Select Data Folder', command=self.set_folder,
        font=option_font)
        self.path_textbox = Entry(text='')
        self.path_button.bind('<Button-1>', self.set_folder)
        self.path_button.grid(row=0, column=0, columnspan=1, sticky=W+E+N+S, padx=10, pady=10)
        self.path_textbox.grid(row=0, column=1, columnspan=6, sticky=W+E+N+S, padx=10, pady=10)

        ### OPEN LIMITS FILE DIALOG -- select filepath for limit analysis
        self.limits_file = StringVar()
        self.limits_button = Button(text='Select Limits File', command=self.set_limits,
        font=option_font)
        self.limits_textbox = Entry(text='')
        self.limits_button.bind('<Button-1>', self.set_limits)
        self.limits_button.grid(row=1, column=0, columnspan=1, sticky=W+E+N+S,
        padx=10, pady=10)
        self.limits_textbox.grid(row=1, column=1, columnspan=6, sticky=W+E+N+S,
        padx=10, pady=10)

        ### CHECKBOXES TEMPS -- select temperatures
        Label(text="Temps:", font=label_font, bg=bg_color).grid(row=2, column=0,
         sticky=E+N+S, pady=10)
        self.tmp1, self.tmp2, self.tmp3, self.tmp4, self.tmp5 = -40, 23, 45, 60, 85
        self.tmp1_onoff = IntVar()
        self.tchk1 = Checkbutton(master, text="-40C", variable=self.tmp1_onoff,
         font=option_font, bg=bg_button, indicatoron=0,
         borderwidth=2, selectcolor="yellow")
        self.tmp2_onoff = IntVar()
        self.tchk2 = Checkbutton(master, text="23C", variable=self.tmp2_onoff,
         font=option_font, bg=bg_button, indicatoron=0,
         borderwidth=2, selectcolor="yellow")
        self.tmp3_onoff = IntVar()
        self.tchk3 = Checkbutton(master, text="45C", variable=self.tmp3_onoff,
         font=option_font, bg=bg_button, indicatoron=0,
         borderwidth=2, selectcolor="yellow")
        self.tmp4_onoff = IntVar()
        self.tchk4 = Checkbutton(master, text="60C", variable=self.tmp4_onoff,
         font=option_font, bg=bg_button, indicatoron=0,
         borderwidth=2, selectcolor="yellow")
        self.tmp5_onoff = IntVar()
        self.tchk5 = Checkbutton(master, text="85C", variable=self.tmp5_onoff,
         font=option_font, bg=bg_button, indicatoron=0,
         borderwidth=2, selectcolor="yellow")
        tmp_i = 1  ## start at 2nd column
        for chk in [self.tchk1, self.tchk2, self.tchk3, self.tchk4, self.tchk5]:
            chk.grid(row=2, column=tmp_i, sticky=W+E+N+S, pady=10)
            tmp_i += 1
        self.temp_pairs = [(self.tmp1_onoff, self.tmp1), (self.tmp2_onoff, self.tmp2),
          (self.tmp3_onoff, self.tmp3), (self.tmp4_onoff, self.tmp4),
          (self.tmp5_onoff, self.tmp5)]
        self.temps = []

        ### CHECKBOXES BOARDS -- select boards to analyze
        Label(text="Boards:", font=label_font, bg=bg_color).grid(row=3, column=0,
        sticky=E+N+S, pady=10)
        self.on_boards = StringVar()
        self.b1 = IntVar()
        self.chk1 = Checkbutton(master, text="B1", variable=self.b1, font=option_font,
        bg=bg_button, indicatoron=0, borderwidth=2, selectcolor="yellow",
        activebackground=bg_hover, activeforeground=bg_hover)
        self.b2 = IntVar()
        self.chk2 = Checkbutton(master, text="B2", variable=self.b2, font=option_font,
        bg=bg_button, indicatoron=0, borderwidth=2, selectcolor="yellow")
        self.b3 = IntVar()
        self.chk3 = Checkbutton(master, text="B3", variable=self.b3, font=option_font,
        bg=bg_button, indicatoron=0, borderwidth=2, selectcolor="yellow")
        self.b4 = IntVar()
        self.chk4 = Checkbutton(master, text="B4", variable=self.b4, font=option_font,
        bg=bg_button, indicatoron=0, borderwidth=2, selectcolor="yellow")
        self.b5 = IntVar()
        self.chk5 = Checkbutton(master, text="B5", variable=self.b5, font=option_font,
        bg=bg_button, indicatoron=0, borderwidth=2, selectcolor="yellow")
        self.b6 = IntVar()
        self.chk6 = Checkbutton(master, text="B6", variable=self.b6, font=option_font,
        bg=bg_button, indicatoron=0, borderwidth=2, selectcolor="yellow")
        self.boards = [self.b1, self.b2, self.b3, self.b4, self.b5, self.b6]
        brd_i = 1  ## start at 2nd column
        for chk in [self.chk1, self.chk2, self.chk3, self.chk4, self.chk5, self.chk6]:
            chk.grid(row=3, column=brd_i, sticky=W+E+N+S, pady=10)
            brd_i += 1

        ### CHECKBUTTONS -- select analysis tasks (plot, stats, or plot&stats)
        Label(text="Analysis Type:", font=label_font, bg=bg_color).grid(row=4, column=0,
         sticky=E+N+S, pady=10)
        self.stats = IntVar()
        self.rad1 = Checkbutton(master, text="Tables/Stats", variable=self.stats, font=option_font,
        bg=bg_button, indicatoron=0, borderwidth=2, selectcolor="yellow")
        self.plots = IntVar()
        self.rad2 = Checkbutton(master, text="Plots", variable=self.plots, font=option_font,
        bg=bg_button, indicatoron=0, borderwidth=2, selectcolor="yellow")
        self.hists = IntVar()
        self.rad3 = Checkbutton(master, text="Histograms", variable=self.hists, font=option_font,
        bg=bg_button, indicatoron=0, borderwidth=2, selectcolor="yellow")
        rad_i = 1  ## start at 2nd column
        for rad in [self.rad1, self.rad2, self.rad3]:
            rad.grid(row=4, column=rad_i, sticky=W+E+N+S, pady=10)
            rad_i += 1

        ### ENTRY ANALYSIS CSV -- textfield entry for name of csv analysis file
        self.analysis_filename = StringVar()
        Label(text="Analysis Filename:", font=label_font, bg=bg_color).grid(row=5,
         column=0, sticky=E+N+S, pady=10)
        Entry(textvariable=self.analysis_filename).grid(row=5, column=1, columnspan=5,
         sticky=W+E+N+S, padx=10, pady=10)

        ### BUTTON ANALYZE -- analyze data based on user entered parameters
        self.analyze_button = Button(master, text="Analyze", command=self.analyze,
        font=big_btn_font, bg="green", fg="white")
        self.analyze_button.grid(row=6, column=3, columnspan=1, sticky=W+E+N+S,
        padx=10, pady=10)

        ### BUTTON QUIT -- quit the application
        self.close_button = Button(master, text="Exit", command=master.quit,
          font=big_btn_font, bg="red", fg="white")
        self.close_button.grid(row=7, column=6, sticky=W+E+S, padx=10, pady=10)

    def set_folder(self, event):
        directory = filedialog.askdirectory()
        self.folderpath.set(directory)
        self.path_textbox.delete(0, END)
        self.path_textbox.insert(0, self.folderpath.get())

    def set_limits(self, event):
        filename = filedialog.askopenfilename()
        self.limits_file.set(filename)
        self.limits_textbox.delete(0, END)
        self.limits_textbox.insert(0, self.limits_file.get())

    def set_boards(self):
        ## retrieves on_board numbers
            ## TO DO: change board number identification logic
        bnums = ''
        for board in self.boards:
            b_number = ''
            if board.get() == 1:
                if board == self.b1:
                    print('B1 present')
                    b_number = '1'
                elif board == self.b2:
                    print('B2 present')
                    b_number = '2'
                elif board == self.b3:
                    print('B3 present')
                    b_number = '3'
                elif board == self.b4:
                    print('B4 present')
                    b_number = '4'
                elif board == self.b5:
                    print('B5 present')
                    b_number = '5'
                elif board == self.b6:
                    print('B6 present')
                    b_number = '6'
            bnums += b_number
        self.on_boards.set(bnums)

    def set_temps(self):
        self.temps = []
        for temp in self.temp_pairs:
            if temp[0].get() == 1:
                self.temps.append(temp[1])

    def set_csv_name(self):
        self.analysis_filename.set()

    def analyze(self):
        self.set_boards()
        self.set_temps()
        print("\nAnalysis Params:")
        print(self.folderpath.get())
        print(self.limits_file.get())
        print("Temps:", self.temps)
        print("Boards:", self.on_boards.get())
        print("Analysis Filename:", self.analysis_filename.get())
        ## pull limits from limits file
        print("Limits:\n")
        wb = self.limits_file.get()
        ws = "Sheet1"
        limits = Limits(wb, ws)
        print('\n\n')
        do_analysis(self.analysis_filename.get(), self.folderpath.get(), self.on_boards.get(),
        limits, self.stats.get(), self.plots.get(), self.hists.get(), *self.temps)

root = Tk()
my_gui = DataAnalysis(root)
for i in range(7):
    Grid.columnconfigure(root, i, weight=3, uniform='col')
root.configure(background=bg_color)
root.mainloop()
