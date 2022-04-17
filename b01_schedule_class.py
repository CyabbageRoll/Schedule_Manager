# %% =======================================================================
# import libraries
#===========================================================================
# default
import os
import bisect
import hashlib
import datetime
from collections import defaultdict 
from distutils.util import strtobool

# pip or conda install
import pandas as pd
import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import popup_get_date

# user
from b01_schedule_class_base import ScheduleManageBase
from c01_func_priority_calculation import SortTickets

# %% =======================================================================
# class
#===========================================================================

class ScheduleManage(ScheduleManageBase):

    def __init__(self):

        self.prj_dfs = {}
        self.sch_dfs = {}
        self.trk_dfs = {}
        self.pln_dfs = {}
        self.sizes = {}
        self.param = {}
        self.colors = {}
        self.previous_selected_ticket = None
        self.values = None
        self._initialize() 
        self.app_schedule = [""] * self.param["dailytable_rows"]


    def _initialize(self):

        ret = self._read_settings_file()
        if ret:
            sg.popup_ok(f"Input parameter {ret} is wrong.")

        self.param["columns"] = [
                                 "Project1", "Project2", "Task", "Ticket", "Detail", "Is_Task",
                                 "Ready_date", "Due_date", "Estimation", "Update_Estimation",
                                 "In_charge",
                                 "Prev_task", "Next_task",
                                 "Status",
                                 "Begin_date_reg", "End_date_reg", "Man_hour_reg",
                                 "File_path", "Comment",
                                 "Priority",
                                 "Color",
                                 ]
        self.param["hash_item"] = ["Project1", "Project2", "Task", "Ticket", "In_charge"]
        self.param["priority_list"] = ["Project1", "Project2", "Task", "Ticket", "In_charge", "Ready_date", "Due_date", "Status", "Priority"]
        self.param["schedule_add_info"] = ["Hour", "Health", "Safety", "Reasons_overwork", "Information", "Memo1", "Memo2", "Memo3"]
        self.param["status"] = ["ToDo", "Doing", "Checking", "Done", "Pending"]

        self.sizes["header_clm_chk"] = (self.sizes["window"][0] // 20 * 12, self.sizes["window"][1] // 20 *  2)
        self.sizes["header_clm_btn"] = (self.sizes["window"][0] // 20 *  1, self.sizes["window"][1] // 20 *  2)
        self.sizes["header_clm_rdi"] = (self.sizes["window"][0] // 20 *  4, self.sizes["window"][1] // 20 *  2)
        self.sizes["left_tab_group"] = (self.sizes["window"][0] // 20 * 14, self.sizes["window"][1] // 20 * 18)
        self.sizes["left_tab1_canvas"] = (self.sizes["left_tab_group"][0]*10, self.sizes["left_tab_group"][1] // 20 *  3) 
        # self.sizes["left_tab1_calendar"] = (25 ,1) 
        self.sizes["rihgt_tab_group"] = (self.sizes["window"][0] // 20 * 6, self.sizes["window"][1] // 20 * 18)

        # to be move to settings
        # self.sizes["r1_table_width"] = 20
        # self.sizes["r2_table_width"] = [30, 8, 20]
        self.sizes["tbl_row_hight"] = 12
        self.colors["priority_table"] = ["#505050", "#404040", "#303030"]
        
        # read project file
        self._read_prj_file()
        self._read_daily_schedule_file()
        self._read_man_hour_tracker_file()
        self._read_monthly_plan_file()


    def _read_settings_file(self):
        """read setting values from sch_m_setting.csv file.
           1. a directory where dataframe files save -> self.prj/sch/trk_file
           2. parameters of font, num of table of rows...etc -> self.param
           3. valuse of gui size -> self.sizes

        Returns:
            str or bool False
               : if some essential key was not defined in csv file
                 return the key value, else, return False
        """

        self.SETTINGS_DIR = ["file_save_dir"]
        self.SETTINGS_DIR_TYPE = ["s"]
        self.SETTINGS_PARAM = ["window_theme", "header_nrow", "user_name", "team_members", "hour_in_date", "daily_begin", "dailytable_rows", "dailytable_disp_rows", "font", "auto_priority_activate"] 
        self.SETTINGS_PARAM_TYPE = ["s", "i", "s", "s", "i", "i", "i", "i", "si", "b"]
        self.SETTINGS_SIZE = ["window", "header_button", "header_chkbox", "header_radio", "right_button", "right_input", "right_comment_boxies", "right_team_box", "graph_top_right", "left3_col_width", "r1_table_width", "r2_table_width"]
        self.SETTINGS_SIZE_TYPE = ["ii", "ii", "ii", "ii", "ii", "ii", "ii", "ii", "ii", "ii", "i", "iii"]

        df = pd.read_csv("./sch_m_settings.csv", header=None, index_col=0)
        self.df_settings = df
        
        if self.SETTINGS_DIR[0] not in df.index.values.tolist():
            return self.SETTINGS_DIR[0]
        root_dir = df.loc[self.SETTINGS_DIR[0], 1]
        self.prj_file = os.path.join(root_dir, r"prj/prj_file_--name--.pkl")
        self.sch_file = os.path.join(root_dir, r"sch/sch_file_--name--.pkl")
        self.trk_file = os.path.join(root_dir, r"trk/trk_file_--name--.pkl")
        self.pln_file = os.path.join(root_dir, r"pln/pln_file_--name--.pkl")

        for key in self.SETTINGS_PARAM:
            if key not in df.index.values.tolist():
                return key
        self.param["window_theme"] =  df.loc["window_theme", 1]
        self.param["header_nrow"] = int(df.loc["header_nrow", 1])
        self.param["user_name"] =  df.loc["user_name", 1]
        self.param["hour_in_date"] = int(df.loc["hour_in_date", 1])
        self.param["dailytable_rows"] = int(df.loc["dailytable_rows", 1])
        self.param["daily_begin"] = int(df.loc["daily_begin", 1])
        self.param["dailytable_disp_rows"] = int(df.loc["dailytable_disp_rows", 1])
        self.param["font"] = (df.loc["font", 1], int(df.loc["font", 2]))
        # tmp = df.loc["team_members"].values.tolist()
        # self.param["team_members"] = [m for m in tmp if m == m]
        self.param["team_members"] = df.loc["team_members", 1].split(" ")
        self.param["auto_priority_activate"] = bool(strtobool(df.loc["auto_priority_activate", 1]))
        # width, hight

        sizes_keys = self.SETTINGS_SIZE[:10]
        for key in sizes_keys:
            if key not in df.index.values.tolist():
                return key
        for key in sizes_keys:
            self.sizes[key] = (int(df.loc[key, 1]), int(df.loc[key, 2]))
        # rows1
        sizes_keys = self.SETTINGS_SIZE[10:11]
        for key in sizes_keys:
            if key not in df.index.values.tolist():
                return key
        for key in sizes_keys:
            self.sizes[key] = (int(df.loc[key, 1]))
        # rows3
        sizes_keys = self.SETTINGS_SIZE[11:12]
        for key in sizes_keys:
            if key not in df.index.values.tolist():
                return key
        for key in sizes_keys:
            self.sizes[key] = (int(df.loc[key, 1]),int(df.loc[key, 2]),int(df.loc[key, 3]))

        return False


    def create_window(self):
        """create window and refresh tabs after that
            1. bind the mouse control items. (window must be finalized before bind)
            2. warning message is shown if tracking till yesterday is not done
        """

        sg.theme(self.param["window_theme"])
        layout = self._layout()
        self.window = sg.Window('Schedule Manager v20220313', layout, size=self.sizes["window"], font=self.param["font"], finalize=True)
        _, self.values = self.window.read(timeout=1)

        self._bind_items()
        self.update_tabs()
        self._warning_not_done_track_record()


    def update_tabs(self):

        self._priority_update()
        l3_tbl_df = self.prj_dfs[self.param["user_name"]][self.param["priority_list"]]
        self.window["-l3_tbl_00-"].update(values=l3_tbl_df.values.tolist())
        
        if self.values["-l3_cbx_20-"]:
            self.l3_priority_auto_button_pressed()
        
        self._l3_priority_table_update()
        self.l1_chart_draw()
        self._r1_input_box_right_click_menu_defined()
        self.r2_daily_schedule_update()
        self._r2_information_box_update()
        self._r3_display_team_box_update()
        self._r5_multiline_from_df()

    def parse_event(self):
        """read event and return the which location, which item, which id.

        Returns:
            return belows but event is not defined by layout class, return None or 0
            str : event. one of window.read returns
            str : event location like hd (header), r1(right tab 1), l2(left tab 2)
            str : event item like btn(button), rdi(radio) etc...
            int : item id. defined in layout class
            if evnet is l1 or l3 right click menu
                return event, "l1", "grp-RC", ticket id
        """
        event, self.values = self.window.read()

        if not event:
            return event, None, None, 0
        if len(event) <= 2:
            return event, None, None, 0
        if event[-1] == "_":
            # right click menu of l1 graph or l3 table was clicked.
            return event, "l1", "grp-RC", self.previous_selected_ticket
        if event[-1] == ".":
            # right clike menu of r1 input box was clicked
            return event, "r1", "right_menu", event[:4]
        if event[0] != "-" or event[-1] != "-":
            return event, None, None, 0
        

        pos, item, eid = event[1:-1].split("_")
        if len(eid) <= 2:
            eid = int(eid)
        else:
            item = item + eid[2:]
            eid = int(eid[:2])

        return event, pos, item, eid


# ==========================================================================
# functions for header
#===========================================================================
    def header_all_button_pressed(self):
        for cbx in self.hd_cbx:
            cbx.update(value=True)


    def header_clear_button_pressed(self):
        for cbx in self.hd_cbx:
            cbx.update(value=False)


    def header_refresh_button_pressed(self):
        self.update_tabs()


    def header_checkbox_changed(self, eids=[]):
        """
        when one or some of header project check boxis is updated,
        call this function. 
        l1 frame(s) is hided or unhided depend on check box is True or False
        Args:
            eids (list, optional): [description]. Defaults to [].
        """
        if not eids:
            eids = [i for i in range(len(self.prj))]

        for eid in eids:
            if self.hd_cbx[eid].get():
                self.l1_frm[eid][0].unhide_row()
            else:
                self.l1_frm[eid][0].hide_row()


    def header_upload_button_pressed(self):
        """save prj, sch, trk dataframes at user specified location"""
        self._save_prj_file()
        self._save_daily_schedule_file()
        self._save_man_hour_traker_file()
        self._save_monthly_plan_file()


    def header_reload_button_pressed(self):
        """read prj, sch, trk dataframes from user specified location"""
        self._read_prj_file()
        self._read_daily_schedule_file()
        self._read_man_hour_tracker_file()
        self._read_monthly_plan_file()
        self.update_tabs()


    def header_member_raido_button_changed(self):
        self.update_tabs()



# ==========================================================================
# functions for left tabs
#===========================================================================
    # l0 =======================================================================
    def l0_settings_save_and_restart_button_pressed(self):

        settings_list = [self.SETTINGS_DIR, self.SETTINGS_PARAM, self.SETTINGS_SIZE]
        setting_type_list = [self.SETTINGS_DIR_TYPE, self.SETTINGS_PARAM_TYPE, self.SETTINGS_SIZE_TYPE]

        for settings, setting_type in zip(settings_list, setting_type_list):
            for setting, input_type in zip(settings, setting_type):  
                for col, t in enumerate(input_type):
                    self.df_settings.loc[setting, col + 1] = self.values[f"-{setting}_{col:02d}-"]

        self.df_settings.to_csv("./sch_m_settings.csv", header=None)
        self.header_upload_button_pressed()
        self._initialize()
        self.window.close()
        self.create_window()

        return

    # l1 =======================================================================
    def l1_graph_area_clicked(self):
        """in below condition, clicked item is scheduled in daily table
            - activate left click checkbox of r2 tab(daily tab) is activated
            - r2 tab(daily tab) is activeted
            - activated member is same as user
            - ticket is defined in user dataframe
        """
        if not self.values["-r2_cbx_00-"]:
            return
        if self.values["-rt_grp_00-"] != "r2":
            print("daily tab is not acitvated")
            return
        if self._get_activated_member() != self.param["user_name"]:
            print("you can update only your schedule. Other user's daily table is shown now")
            return
        if self._update_sch_dfs(self.previous_selected_ticket):
            self.r2_daily_schedule_update()
        return
    

    def l1_graphs_capture_mouse_motion(self, eid):
        """get mouse xy coordinate in graph area which mouse is above 
        and display the detail of ticket on r1 tab. 
        Remain ticket id for use next other event like right click menu. 

        Args:
            eid (int): graph id which mouse is above
        """
        self.mouse_x = int(self.l1_grp[eid].user_bind_event.x / self.sizes["left_tab1_canvas"][0] * self.sizes["graph_top_right"][0])
        self.mouse_y = int(self.l1_grp[eid].user_bind_event.y / self.sizes["left_tab1_canvas"][1] * self.sizes["graph_top_right"][1])

        # self.graph_positions has each ticket start y coordinate
        pos_index = bisect.bisect_left(self.graph_positions[eid], self.mouse_x)
        ticket_id = self.graph_ticket_ids[eid][pos_index-1]
        if not ticket_id:
            return

        self.previous_selected_ticket = ticket_id
        if self.values["-r1_cbx_00-"]:
            return

        flag_is_ticket, mouse_on_prj = self._get_series_from_ticket_id(ticket_id)
        if flag_is_ticket:
            self._r1_inputs_from_df(mouse_on_prj)


    def l1_graph_right_click_menu_selected(self, event, ticket_id):
        """
        Caution! used this method when "L3" right click menu is clicked also 

        Args:
            event (str): one of window read returns
            ticket_id (str): activated ticket id (hash-md5)
        """

        # get ticket information. if ticket is not exist with unexpected reason, "return"
        flag_is_ticket, mouse_on_prj = self._get_series_from_ticket_id(ticket_id)
        if not flag_is_ticket:
            return
        in_charge = mouse_on_prj["In_charge"]
        self._r1_inputs_from_df(mouse_on_prj)

        # Branch processing
        if event[:-1] in self.param["status"]:
            self.prj_dfs[in_charge].loc[ticket_id, "Status"] = event[:-1]
            if event[:-1] == "Done":
                self.get_reason_of_over_estimation_tickets(ticket_ids=[ticket_id], shorter=True)
        
        r_menu = ["Scheduling_", "Edit_", "New ticket FROM this_", "New ticket TO this_"]
        if event == r_menu[0]:
            if self.values["-rt_grp_00-"] != "r2":
                print("daily tab is not acitvated")
                return
            if self._get_activated_member() != self.param["user_name"]:
                print("you can update only your schedule. Other user's daily table is shown now")
                return
            if self._update_sch_dfs(ticket_id):
                self.r2_daily_schedule_update()

        if event in r_menu[1:4]:
            self.values["-r1_cbx_00-"] = True
            self.window["-r1_cbx_00-"].update(self.values["-r1_cbx_00-"])
            if event in r_menu[2:4]:
                self.values["-r1_inp_03-"] = ""
                self.window["-r1_inp_03-"].update("")
                select_row = [i for i, tid in enumerate(self.r1_tables[1]) if tid == ticket_id]
            if event == r_menu[2]:
                self.window["-r1_tbl_02-"].update(select_rows=select_row)
            if event == r_menu[3]:
                self.window["-r1_tbl_03-"].update(select_rows=select_row)
        self.update_tabs()


    def l1_chart_draw(self):
        """
        tickets belongs to activated user are arranged in each project graph area
        tickets xy coordinats are calcurated with self._calc_ticket_position.
        """
        name = self._get_activated_member()
        self._priority_update(name=name)
        self._calc_ticket_position(name)
        
        # draw calendar top of the L1 tab
        begin_day = datetime.date.today()
        l1_calendar = [begin_day + datetime.timedelta(days=i) for i in range(100)]
        txt = [d.strftime("%m/%d(%a)") for d in l1_calendar if d.weekday() < 5]
        self.l1_grp_cal.erase()
        for i, t in enumerate(txt):
            self.l1_grp_cal.draw_text(t, (50+i*100, 50), color="#eeeeee", font=self.param["font"])
            self.l1_grp_cal.draw_line(((i+1)*100, 0), ((i+1)*100, 100), color="#eeeeee", width=1)

        # ticket id and position list. that is used to know which ticket mouse cursol is on
        self.graph_positions = [[0] for i in range(len(self.prj))]
        self.graph_ticket_ids = [[] for i in range(len(self.prj))]

        # drow tickets on each task graph
        for prj_id, prj in enumerate(self.prj):
            self.l1_grp[prj_id].erase()
            ticket_pos_tmp = self.ticket_pos_df[self.ticket_pos_df["prj"] == prj]
            df_tid = ticket_pos_tmp.index.values.tolist()
            iter_list = ticket_pos_tmp[["Task", "Ticket", "begin_pos", "end_pos", "Update_Estimation", "Man_hour_reg", "In_charge", "Color"]].values.tolist()

            for i, (tid, [task, ticket, x0, x1, te, tr, inc, color]) in enumerate(zip(df_tid, iter_list)):
                x0, x1 = int(x0), int(x1)
                y0 = -(i % 3) * 30 + 75
                color = color if color else "#505050"
                self.l1_grp[prj_id].draw_rectangle((x0, y0-12),(x1, y0+12), fill_color=color, line_color=color, line_width=1)
                self.l1_grp[prj_id].draw_text(f" {task}-{ticket}", (x0, y0+6), color="#eeeeee", font=self.param["font"], text_location=sg.TEXT_LOCATION_LEFT)
                self.l1_grp[prj_id].draw_text(f" {inc} ({tr:2.2f}/{te:2.2f})", (x0, y0-6), color="#eeeeee", font=(self.param["font"][0], self.param["font"][1]-2), text_location=sg.TEXT_LOCATION_LEFT)
                
                if self.graph_positions[prj_id][-1] >= x0:
                    self.graph_positions[prj_id].append(x1)
                    self.graph_ticket_ids[prj_id].append(tid)
                else:
                    self.graph_positions[prj_id].extend([x0, x1])
                    self.graph_ticket_ids[prj_id].extend([None, tid])
            self.graph_positions[prj_id].append(999999)
            self.graph_ticket_ids[prj_id].append(None)

        if not self.values:
            return

        for i, ticket_ids in enumerate(self.graph_ticket_ids):
            self.values[f"-hd_cbx_{i:02d}-"] = len(ticket_ids) != 1
            self.window[f"-hd_cbx_{i:02d}-"].update(len(ticket_ids) != 1)
        self.header_checkbox_changed()

    # l2 =======================================================================
    # not implemented

    # l3 =======================================================================
    def l3_priority_updown_button_pressed(self, eid):
        """
        priority of selected ticket is changed depending on the button. 
        And update table
        Args:
            eid (int): button id
        """

        ticket_id = self.l3_get_selected_ticket_id_in_table()
        if not ticket_id:
            return
        # Update the step value prevent overflow
        current_pri = self.prj_dfs[self.param["user_name"]].loc[ticket_id, "Priority"].item()
        steps = [-10, -1, 2, 11]
        step = max(1, current_pri + steps[eid]) - current_pri
        self._priority_update(ticket_id=ticket_id, step=step)
        self._l3_priority_table_update(ticket_id)

        return


    def _l3_priority_table_update(self, ticket_id=None):
        l3_tbl_df = self.prj_dfs[self.param["user_name"]][self.param["priority_list"]]
        row = self.prj_dfs[self.param["user_name"]].index.get_loc(ticket_id) if ticket_id else 0

        table_colors = [[] for _ in range(l3_tbl_df.shape[0])]
        for i, tid in enumerate(l3_tbl_df.index.values.tolist()):
            if l3_tbl_df.loc[tid, "Status"] == "Done":
                table_colors[i] = [i, self.colors["priority_table"][2]]
            elif l3_tbl_df.loc[tid, "Project1"] == "Other" and l3_tbl_df.loc[tid, "Project2"] == "Regularly":
                table_colors[i] = [i, self.colors["priority_table"][1]]
            else:
                table_colors[i] = [i, self.colors["priority_table"][0]]
        self.window["-l3_tbl_00-"].update(values=l3_tbl_df.values.tolist(), select_rows=[row], row_colors=table_colors)


    def l3_table_selected_ticket_changed(self):
        """call this function When a row of left 3 priority table is clicked 
           Display the detail of ticket on r1 tab. 
           Remain ticket id for use next other event like right click menu. 
        """
        ticket_id = self.l3_get_selected_ticket_id_in_table()

        if not ticket_id:
            return
        self.previous_selected_ticket = ticket_id

        if self.values["-r1_cbx_00-"]:
            return

        flag_is_ticket, mouse_on_prj = self._get_series_from_ticket_id(ticket_id)
        if flag_is_ticket:
            self._r1_inputs_from_df(mouse_on_prj)

        if not self.values["-r2_cbx_00-"]:
            return
        if self.values["-rt_grp_00-"] != "r2":
            print("daily tab is not acitvated")
            return
        if self._get_activated_member() != self.param["user_name"]:
            print("you can update only your schedule. Other user's daily table is shown now")
            return
        if self._update_sch_dfs(self.previous_selected_ticket):
            self.r2_daily_schedule_update()
        return


    def l3_get_selected_ticket_id_in_table(self):
        if not self.values["-l3_tbl_00-"]:
            return None
        indices = [self.prj_dfs[self.param["user_name"]].index.values[row] for row in self.values["-l3_tbl_00-"]]
        ticket_id = indices[0]
        return ticket_id


    def l3_priority_auto_button_pressed(self):
        df = self.prj_dfs[self.param["user_name"]].copy()
        df = df[df["Status"] != "Done"]
        df = df.query("Project1 != 'Other' or Project2 != 'Regularly'")

        st = SortTickets(df, self.param["hour_in_date"])
        st.calc_priority()

        for i, tid in enumerate(st.sorted_tid):
            self.prj_dfs[self.param["user_name"]].loc[tid, "Priority"] = i + 1
            # print(df.loc[tid, "Task"], df.loc[tid, "Ticket"], i)

        self._priority_update()
        self._l3_priority_table_update()
        
        print("update")

        return

# ==========================================================================
# functions for right tabs
#===========================================================================
    # r1 =======================================================================
    def r1_input_date_box_selected(self, eid):
        """The input box for date is inputted by using calendar
           
        Args:
            eid (int): input box id defined _r1_layout
        """
        ymd = datetime.date.today()
        ret = popup_get_date(start_year=ymd.year, start_mon=ymd.month, start_day=ymd.day, begin_at_sunday_plus=1, close_when_chosen=True, keep_on_top=True, no_titlebar=False)
        if ret:
            (m, d, y) = ret
            self.values[f"-r1_inp_{eid:02d}-"] = f"{y}/{m}/{d}"
            self.window[f"-r1_inp_{eid:02d}-"].update(self.values[f"-r1_inp_{eid:02d}-"])
        self.r1_input_check()
        return 

    
    def r1_input_check(self):
        """
        checking if values in r1 input box are valid.
        values is valid -> box color set white
        project1,2 and task are inputed but new -> box color set yellow
        valus is invalid -> box color set red

        Returns:
            list : each box error value.
                   0 is "valid", 1 is "valid with caution", 2 is "invalid"
        """

        def update_input_box_color(eid, c):
            colors = ["#ffffff", "#aaaa00", "#aa0000"]  #[white, yellow, red]
            self.window[f"-r1_inp_{eid:02d}-"].update(background_color=colors[c])
            return c

        def can_convert_datetime(str):
            try:
                datetime.datetime.strptime(str, r"%Y/%m/%d")
                return True
            except:
                return False

        def can_convert_float025(str):
            """if value is able to be converted float and is multiple 0.25 True
               (Third decimal place or less is ignored)
            Args:
                str (str): checking inputted strings

            Returns:
                bool : True means able to convert
            """
            try:
                v1 = float(str)
                if int(v1 * 100) % 25:
                    return False
                return True
            except:
                return False


        for i in range(4):
            self.values[f"-r1_inp_{i:02d}-"] = self.values[f"-r1_inp_{i:02d}-"].replace(" ", "").replace("　", "")
            self.window[f"-r1_inp_{i:02d}-"].update(self.values[f"-r1_inp_{i:02d}-"])

        # if input values is new, cell color is changed to yellow
        prj1 = self.values[f"-r1_inp_00-"]
        prj2 = self.values[f"-r1_inp_01-"]
        exist_prj_1 = prj1 in self.dic_prj1_2.keys()
        prj2_candidates = self.dic_prj1_2[prj1] if exist_prj_1 else []
        exist_prj_2 = prj2 in prj2_candidates
        exist_prj_12 = f"{prj1}-{prj2}" in self.dic_prj_task.keys()
        task_candidates = self.dic_prj_task[f"{prj1}-{prj2}"] if exist_prj_12 else []

        errors = [2] * len(self.r1_inp)
        errors[0] = 0 if exist_prj_1 else 1
        errors[0] = 2 if prj1 == "" else errors[0]
        errors[1] = 0 if exist_prj_2 else 1
        errors[1] = 2 if prj2 == "" else errors[1]
        errors[2] = 0 if self.values[f"-r1_inp_02-"] in task_candidates else 1
        errors[2] = 2 if self.values[f"-r1_inp_02-"] == "" else errors[2]
        errors[3] = 2 if self.values[f"-r1_inp_03-"] == "" else 0
        errors[4] = 0 if can_convert_datetime(self.values[f"-r1_inp_04-"]) else 2
        errors[4] = 0 if self.values[f"-r1_inp_04-"] == "" else errors[4]
        errors[5] = 0 if can_convert_datetime(self.values[f"-r1_inp_05-"]) else 2
        errors[5] = 0 if self.values[f"-r1_inp_05-"] == "" else errors[5]
        errors[6] = 0 if can_convert_float025(self.values[f"-r1_inp_06-"]) else 2
        errors[7] = 0 if can_convert_float025(self.values[f"-r1_inp_07-"]) else 2
        errors[8] = 0
        errors[9] = 0
        errors[10] = 0

        for eid in range(len(self.r1_inp)):
            update_input_box_color(eid, errors[eid])

        self._r1_input_box_right_click_menu_defined()

        return errors


    def r1_apply_button_pressed(self):
        """ticket contents update or create new
        """
        def error_popup(errors):            
            """checking if input values are valid
            Args:
                errors (list): the returns of checking r1 input boxes
            Returns
                int : 0 is "no problem", 1 is "update is canceled"
                      -1 is "ok but project1 or|and 2 is|are new 
                        -> header check boxes need to be updated
            """
            if max(errors) == 2:
                sg.popup("the value in red cell is wrong")
                return 1
            if max(errors) == 1:
                oc = sg.popup_ok_cancel("Project1-Project2-Task is not exits. Do you want to create new?")
                if oc != "OK":
                    return 1
                if errors[0] == 1 or errors[1] == 1:
                    return -1
            return 0

        errors = self.r1_input_check()
        ep = error_popup(errors)
        if ep > 0:
            return

        # create new ticket dataframe from r1 input panel
        input_df = self._df_from_r1_inputs()
        ticket_id = input_df.index
        in_charge = input_df["In_charge"].item()
        if ticket_id in self.prj_dfs[in_charge].index.values.tolist():
            oc = sg.popup_ok_cancel("Same ticket has been existed. Do you want to update this task ?")
            if oc != "OK":
                return
            if in_charge != self.param["user_name"]:
                sg.popup_ok("you can update only your ticket")
                return
            input_df["Priority"] = self.prj_dfs[in_charge].loc[ticket_id, "Priority"]
            self.prj_dfs[in_charge].loc[ticket_id] = input_df.loc[ticket_id]
            self._r1_update_prev_next_task(input_df)
            sg.popup_no_buttons("ticket has been updated", auto_close=True, auto_close_duration=1)                    
            self.update_tabs()
            self._r1_pre_next_ticket_table_update()
            return
            
        print("create new ticket")
        # if input_df["Ticket"].values:
        self.prj_dfs[in_charge] = self.prj_dfs[in_charge].append(input_df)
        self._r1_update_prev_next_task(input_df)

        sg.popup_no_buttons("new ticket has been added", auto_close=True, auto_close_duration=1)

        # update current exist prj dictionaries
        prj = "-".join([input_df["Project1"].item(), input_df["Project2"].item()])
        self.dic_prj1_2[input_df["Project1"].item()].add(input_df["Project2"].item())
        self.dic_prj_task[prj].add(input_df["Task"].item())
        self.prj = sorted(list(self.dic_prj_task.keys()))

        if ep == -1:
            self.window.close()
            self.create_window()
        else:
            self.update_tabs()
            self._r1_pre_next_ticket_table_update()

        return


    def r1_delete_button_pressed(self):
        """delete the ticket
        1. read input boxes imformation and identify the ticket id
        2. if mon hour recode of the ticket is NOT 0, stop deleting.
        3. delete ticket
        4. delete ticket id in TO, FROM of oppnent tickets.  
        """

        # 1. ticket id
        input_df = self._df_from_r1_inputs()
        ticket_id = input_df.index
        user_name = self.param["user_name"]
        if input_df["In_charge"].item() != user_name:
            sg.popup_ok("you can delete only your ticket")
            return 

        # 2. exist recode
        if self.prj_dfs[user_name].loc[ticket_id, "Man_hour_reg"].item() != 0:
            sg.popup_ok("CNA NOT delete. this ticket has been already tracked in recode.")
            return

        # 3. delete ticket
        self.prj_dfs[user_name] = self.prj_dfs[user_name].drop(ticket_id)

        # 4. TO, FROM
        for tid in self.prj_dfs[user_name].index:
            prev_task = self.prj_dfs[user_name].loc[tid, "Prev_task"].split(",")
            next_task = self.prj_dfs[user_name].loc[tid, "Next_task"].split(",")

            if ticket_id in prev_task:
                prev_task.remove(ticket_id)
                self.prj_dfs[user_name].loc[tid, "Prev_task"] = ",".join(prev_task)
            if ticket_id in next_task:
                next_task.remove(ticket_id)
                self.prj_dfs[user_name].loc[tid, "Next_task"] = ",".join(next_task)
        self.update_tabs()


    def _r1_update_prev_next_task(self, input_df):
        """update the tickets which are selected as previous or next ticket of new ticket 
           add new ticket id to "next ticket" of "previous ticket".
           add new ticket id to "previous ticket" of "next ticket".
        Args:
            input_df (pandas dataframe): update or new ticket dataframe
        """
        new_ticket = input_df.index.item()
        prev_tickets = input_df.loc[new_ticket, "Prev_task"].split(",")
        next_tickets = input_df.loc[new_ticket, "Next_task"].split(",")
        name = input_df["In_charge"].item()

        for prev_ticket in prev_tickets:
            if prev_ticket not in self.prj_dfs[name].index.values.tolist():
                continue
            tmp = self.prj_dfs[name].loc[prev_ticket, "Next_task"]
            tmp = tmp.split(",")
            if new_ticket in tmp:
                continue
            tmp.append(new_ticket)
            self.prj_dfs[name].loc[prev_ticket, "Next_task"] = ",".join(tmp)

        for next_ticket in next_tickets:
            if next_ticket not in self.prj_dfs[name].index.values.tolist():
                continue
            tmp = self.prj_dfs[name].loc[next_ticket, "Prev_task"]
            tmp = tmp.split(",")
            if new_ticket in tmp:
                continue
            tmp.append(new_ticket)
            self.prj_dfs[name].loc[next_ticket, "Prev_task"] = ",".join(tmp)


    def _r1_inputs_from_df(self, df):
        """r1 tab (ticket tab) content update from dataframe values

        Args:
            df (pd.Series): self.prj_dfs[name][ticket_id]
        """
        input_values = [df["Project1"], df["Project2"], df["Task"], df["Ticket"],
                        df["Ready_date"], df["Due_date"], df["Estimation"], df["Update_Estimation"] - df["Estimation"],
                        df["File_path"], df["Detail"], df["Comment"]
                       ]
        # input_values = [d.item() if not d.empty else "" for d in input_values]
        input_values = [d for d in input_values]

        for i in range(len(self.r1_inp)):
            k = f"-r1_inp_{i:02d}-"
            self.values[k] = input_values[i]
            self.window[k].update(self.values[k])

        k = "-r1_cmb_00-"
        self.values[k] = df["In_charge"]
        self.window[k].update(self.values[k])
        k = "-r1_cmb_01-"
        self.values[k] = df["Status"]
        self.window[k].update(self.values[k])

        self._r1_pre_next_ticket_table_update()


    def _df_from_r1_inputs(self):
        """create dataframe from values of r1 tab(ticket tab)

        Returns:
            pd.DataFrame: columns is same as each dataframe of self.prj_dfs
        """
        ticket_new = [
                      "0:Project1", "1:Project2", "2:Task", "3:Ticket", "4:Detail", "5:is_Task",
                      "6:Ready_date", "7:Due_date", "8:Estimation", "9:Update_Estimation",
                      "10:In_charge",
                      "11:Prev_task", "12:Next_task",
                      "13:Status",
                      "14:Begin_date_reg", "15:End_date_reg", "16:Man_hour_reg",
                      "17:File_path", "18:Comment",
                      "19:Priority",
                      "20:Color",
                      ]

        r1_inps = [self.values[f"-r1_inp_{i:02d}-"] for i in range(len(self.r1_inp))]

        # previous and next task
        prev_ticket = [self.r1_tables[1][i] for i in self.values["-r1_tbl_02-"] if i]
        next_ticket = [self.r1_tables[1][i] for i in self.values["-r1_tbl_03-"] if i]
        prev_ticket = ",".join(prev_ticket)
        next_ticket = ",".join(next_ticket)

        def float025(s):
            return int(float(s) * 100) / 100

        ticket_new[0:4] = r1_inps[0:4]
        ticket_new[4] = r1_inps[9]
        ticket_new[5] = False
        ticket_new[6:8] = r1_inps[4:6]
        ticket_new[8] = float025(r1_inps[6])
        ticket_new[9] = sum(list(map(float025, r1_inps[6:8])))
        ticket_new[10] = self.values["-r1_cmb_00-"]
        ticket_new[11] = prev_ticket
        ticket_new[12] = next_ticket
        ticket_new[13] = self.values["-r1_cmb_01-"]
        ticket_new[14:16] = [""]*2
        ticket_new[16] = 0
        ticket_new[17] = r1_inps[8]
        ticket_new[18] = r1_inps[10]
        ticket_new[19] = 0
        ticket_new[20] = self._define_ticket_color(*ticket_new[0:3])
        index = self._str_to_hash_id(ticket_new, self.param["columns"])
        
        return pd.DataFrame([ticket_new], columns=self.param["columns"], index=[index])


    def _r1_pre_next_ticket_table_update(self):
        """
        1. read r1 input box items 
        2. make list which has task-tickets in current prj and show r1 table
        3. select table rows which are defined in current ticket 
           if current ticket prev or next ticket is defined. 
        """
        prj1 = self.values[f"-r1_inp_00-"]
        prj2 = self.values[f"-r1_inp_01-"]
        task = self.values[f"-r1_inp_02-"]
        tckt = self.values[f"-r1_inp_03-"]
        name = self.values[f"-r1_cmb_00-"]

        # selected_prev = self.values["-r1_tbl_02-"]
        # selected_next = self.values["-r1_tbl_03-"]

        df_tmp = self.prj_dfs[name].sort_values("Priority")
        df_tmp = df_tmp.query(f"Project1 == '{prj1}' & Project2 == '{prj2}' & Status != 'Done'").copy()
        df_tmp["task-ticket"] = df_tmp['Task'] + "-" + df_tmp['Ticket']
        tickets = df_tmp["task-ticket"].values.tolist()
        tids = df_tmp.index.tolist()
        self.r1_tables = (["None"] + tickets, ["None"] + tids)

        df_tmp = df_tmp.query(f"Task == '{task}' & Ticket == '{tckt}'")
        if not df_tmp.empty:
            current_ticket_id = df_tmp.index.item()
            prev_tckt = self.prj_dfs[name].loc[current_ticket_id, "Prev_task"].split(",")
            next_tckt = self.prj_dfs[name].loc[current_ticket_id, "Next_task"].split(",")
            def_perv = [i for i, tid in enumerate(self.r1_tables[1]) if tid in prev_tckt]
            def_next = [i for i, tid in enumerate(self.r1_tables[1]) if tid in next_tckt]
        else:
            def_perv = []
            def_next = []

        self.window["-r1_tbl_02-"].update(values=self.r1_tables[0], select_rows=def_perv)
        self.window["-r1_tbl_03-"].update(values=self.r1_tables[0], select_rows=def_next)

        return


    def _r1_input_box_right_click_menu_defined(self):

        menu1 = ["prj1", [f"Prj1:{k}." for k in self.dic_prj1_2.keys()]]
        self.window["-r1_inp_00-"].set_right_click_menu(menu1)
        prj1 = self.values["-r1_inp_00-"]
        if  prj1 not in self.dic_prj1_2.keys():
            return
        
        menu2 = ["prj2", [f"Prj2:{k}." for k in self.dic_prj1_2[prj1]]]
        self.window["-r1_inp_01-"].set_right_click_menu(menu2)
        prj2 = self.values["-r1_inp_01-"]
        if prj2 not in self.dic_prj1_2[prj1]:
            return

        menu3 = ["task", [f"Task:{k}." for k in self.dic_prj_task[f"{prj1}-{prj2}"]]]
        self.window["-r1_inp_02-"].set_right_click_menu(menu3)


    def r1_right_click_menu_clicked(self, event):

        text = event[5:-1]
        if event[:4] == "Prj1":
            self.values["-r1_inp_00-"] = text
            self.window["-r1_inp_00-"].update(text)
        if event[:4] == "Prj2":
            self.values["-r1_inp_01-"] = text
            self.window["-r1_inp_01-"].update(text)
        if event[:4] == "Task":
            self.values["-r1_inp_02-"] = text
            self.window["-r1_inp_02-"].update(text)

        self.r1_input_check()

    # r2 =======================================================================
    def r2_daily_schedule_update(self):
        """update r2 daily schedule table. 
        r2 information box and r3 team box are also updated
        """
        r2_tbl, table_colors, r2_working_hour = self._r2_create_schedule_table()
        self.values["-r2_txt_03-"] = r2_working_hour
        self.window["-r2_txt_03-"].update(r2_working_hour)
        self.window["-r2_tbl_00-"].update(values=r2_tbl, row_colors=table_colors)
        self._r2_information_box_update()
        self._r3_display_team_box_update()
        return


    def _r2_create_schedule_table(self):
        """create the table which is displayed in r2 daily table
        column 0 is daily schedule contents get form self.sch_dfs[member]
        column 1 is time table (09:30~) created in here
        column 2 is meeting information get from self.app_schedule

        Returns:
            list(list): daily schedule contents displayed in r2 daily table
            list : table colors
            str: working time
        """
        # base table color
        colors_4 = ["#888888", "#808080", "#787878", "#707070"]
        table_colors = [(i, colors_4[i%4]) for i in range(self.param["dailytable_rows"])]

        # get each table data
        sch_col = self.window["-r2_txt_02-"].get()
        sch_user = [""] * (24*4)
        name = self._get_activated_member()
        if sch_col not in self.sch_dfs[name].columns.values.tolist():
            self.sch_dfs[name][sch_col] = ""
        sch_user = self.sch_dfs[name][sch_col].tolist()[:24*4]
        sch_time = [f"{self.param['daily_begin']+i//4:02d}:{i%4*15:02d} ~" for i in range(self.param["dailytable_rows"])]
        sch_user = sch_user[self.param["daily_begin"]*4:self.param["daily_begin"]*4+self.param["dailytable_rows"]]
        sch_appl = self.app_schedule

        # combine same task
        nrows = len(sch_user)-1
        work_rows = []
        MAKER_CONTINUE = "↓"
        for i in range(nrows):
            if sch_user[nrows-i] == "":
                continue
            if sch_user[nrows-i] == sch_user[nrows-i-1]:
                    sch_user[nrows-i] = MAKER_CONTINUE
            work_rows.append(nrows-i)
        if sch_user[0] != "":
            work_rows.append(0)
        
        # define table color and ticket id is changed into name
        i = -1
        while i < nrows-1:
            i += 1
            if sch_user[i] == "":
                continue
            if sch_user[i] == MAKER_CONTINUE:
                table_colors[i] = (i, table_colors[i-1][1])
                continue

            flag_is_ticket, ticket_df = self._get_series_from_ticket_id(sch_user[i])
            if not flag_is_ticket:
                continue
            c = ticket_df["Color"]
            if sch_user[i+1] == MAKER_CONTINUE:
                sch_user[i] = "-".join(map(str, ticket_df[["Project1", "Project2"]].tolist()))
                sch_user[i+1] = "-".join(map(str, ticket_df[["Task", "Ticket"]].tolist()))
                table_colors[i] = (i,c)
                table_colors[i+1] = (i+1, c)
                i += 1
                continue
            else:
                sch_user[i] = "-".join(map(str, ticket_df[["Task", "Ticket"]].tolist()))
                table_colors[i] = (i, c)
                continue

        # create schedule table
        r2_tbl = [[a, t, u] for a, t, u in zip(sch_user, sch_time, sch_appl)]
        
        # calculate working_hour
        if work_rows:
            t_begin = min(work_rows)*0.25 + self.param["daily_begin"]
            t_end = (max(work_rows)+1)*0.25 + self.param["daily_begin"]
            t_total = len(work_rows)*0.25
            t_break = t_end - t_begin - t_total 
        else:
            t_begin, t_end, t_total, t_break = 0, 0, 0, 0

        def x2h(x): return f"{int(x):02d}:{int((x - int(x)) * 0.6 * 100 + 0.1):02d}"
        r2_working_hour = f"     {x2h(t_begin)}   ~   {x2h(t_end)}   ({x2h(t_total)})   <{x2h(t_break)}>"
        self.sch_dfs[name].loc["Hour", sch_col] = r2_working_hour

        return r2_tbl, table_colors, r2_working_hour


    def r2_get_schedule_from_app_button_pressed(self):
        print("not implemented")
        return


    def r2_delete_button_pressed(self):
        if self._get_activated_member() != self.param["user_name"]:
            sg.popup_ok("you can update only your schedule. Other user's daily table is shown now")
            return
        if self._update_sch_dfs(ticket_id=""):
            self.r2_daily_schedule_update()
        return


    def r2_date_txt_pressed(self):
        ymd = datetime.date.today()
        ret = popup_get_date(start_year=ymd.year, start_mon=ymd.month, start_day=ymd.day, begin_at_sunday_plus=1, close_when_chosen=True, keep_on_top=True, no_titlebar=False)
        if ret:
            (m, d, y) = ret
            self.window[f"-r2_txt_02-"].update(f"{y:04d}/{m:02d}/{d:02d}")
            self.r2_daily_schedule_update()
            self._r2_information_box_update()
        return


    def r2_save_record_button_pressed(self):
        """
        Record the daily working hour for each ticket
        1. update self.trk_dfs[user]
            at first, every value of selected date column are set 0.
            And the working hour of each tickets in daily table is inputed.
        2. update self.sch_dfs[user]
            Recalcurate total working hour "Man_hour_reg" from self.trk dataframe.
            The first day and the last day of days with work record 
            is set "Begin_date_reg" and "End_date_reg" respectively.
        """
        name = self.param["user_name"]
        col = self.window["-r2_txt_02-"].get()
        # Exception handling
        if self._get_activated_member() != name:
            return
        if datetime.date(*list(map(int, col.split("/")))) > datetime.date.today():
            return
        if col not in self.sch_dfs[name].columns.values.tolist():
            return
        
        # calcurate workin hour of each tikect exist in table 
        sch_user = self.sch_dfs[name][col].tolist()
        sch_user = sch_user[:24*4]
        id_hours = {}
        for ticket_id in sch_user:
            if ticket_id in id_hours:
                id_hours[ticket_id] += 0.25
            elif ticket_id != "":
                id_hours[ticket_id] = 0.25

        update_tickets = set() 
        # daily table had been already traked, tickets in table are added in update "set"
        if col in self.trk_dfs[name].columns.values.tolist():
            update_tickets = set(self.trk_dfs[name][col].index.values.tolist())
        self.trk_dfs[name][col] = 0.0
        for ticket_id in id_hours:
            if ticket_id not in self.trk_dfs[name].index.values.tolist():
                self.trk_dfs[name].loc[ticket_id] = 0
            self.trk_dfs[name].loc[ticket_id, col] = id_hours[ticket_id]
            update_tickets.add(ticket_id)

        for ticket_id in update_tickets:
            ticket_record_se = self.trk_dfs[name].loc[ticket_id] 
            did_date = ticket_record_se[ticket_record_se > 0].index.values.tolist()
            did_date.sort()
            self.prj_dfs[name].loc[ticket_id, "Man_hour_reg"] = ticket_record_se.sum()
            self.prj_dfs[name].loc[ticket_id, "Begin_date_reg"] = did_date[0] if did_date else ""
            self.prj_dfs[name].loc[ticket_id, "End_date_reg"] = did_date[-1] if did_date else ""

        self.update_tabs()
        self.header_upload_button_pressed()
        self.get_reason_of_over_estimation_tickets(ticket_ids=update_tickets)


    def r2_information_box_inputed(self):
        """
        call this method when r2 information input boxes below daily table value is updated
        if activate member was user, working time and reason of overwork copied to team tab
        """
        name = self.param["user_name"]
        col = self.window["-r2_txt_02-"].get()
        # Exception handling
        if self._get_activated_member() != name:
            return
        if col not in self.sch_dfs[name].columns.values.tolist():
            self.sch_dfs[name][col] = ""
        self.sch_dfs[name].loc["Hour", col] = self.window["-r2_txt_03-"].get()
        for i, idx in enumerate(self.param["schedule_add_info"][1:]):
            self.sch_dfs[name].loc[idx, col] = self.values[f"-r2_inp_{i:02d}-"]        
        
        self._r3_display_team_box_update()
        return


    def _r2_information_box_update(self):
        """Read self.sch_dfs[member] and update r2 information box 
        when activate user or date is changed
        """
        # initialize
        for i, idx in enumerate(self.param["schedule_add_info"][1:]):
            self.values[f"-r2_inp_{i:02d}-"] = ""
            self.window[f"-r2_inp_{i:02d}-"].update("")

        name = self._get_activated_member()
        col = self.window["-r2_txt_02-"].get()
        if col not in self.sch_dfs[name].columns.values.tolist():
            return
        for i, idx in enumerate(self.param["schedule_add_info"][1:]):
            self.values[f"-r2_inp_{i:02d}-"] = self.sch_dfs[name].loc[idx, col]
            self.window[f"-r2_inp_{i:02d}-"].update(self.values[f"-r2_inp_{i:02d}-"])

        return

    # r3 =======================================================================
    def _r3_display_team_box_update(self):
        """update r3 team box when contents are updated
        """
        today = datetime.date.today()
        col = datetime.datetime.strftime(today, r"%Y/%m/%d")

        tmp_work = [f"name  :      Begin   ~    End    (Total)   <Break> :  reason for overwork"]
        tmp_info = []
        for i, name in enumerate(self.param["team_members"]):
            if col not in self.sch_dfs[name].columns.values.tolist():
                continue
            hour = self.sch_dfs[name].loc['Hour', col]
            reason = self.sch_dfs[name].loc['Reasons_overwork', col]
            tmp_work.append(f"{name} : {hour} : {reason}")
            tmp_info.append(name)
            tmp_info.append(f"Health : {self.sch_dfs[name].loc['Health', col]}")
            tmp_info.append(f"Safety : {self.sch_dfs[name].loc['Safety', col]}")
            tmp_info.append(f"Information : {self.sch_dfs[name].loc['Information', col]}")

        # working hour box
        txt = "\n".join(tmp_work)
        self.values["-r3_mul_00-"] = txt
        self.window["-r3_mul_00-"].update(txt)

        # information box
        txt = "\n".join(tmp_info)
        self.values["-r3_mul_01-"] = txt
        self.window["-r3_mul_01-"].update(txt)


    def r3_mail_button_pressed(self):
        print("please create function")

    def r3_folder_button_pressed(self):
        print("please create function")

    def r3_memo_button_pressed(self):
        print("please create function")


    # r4 =======================================================================

    # r5 =======================================================================
    def _r5_multiline_from_df(self):
        """plan tab display the monthly and weekly plan saved in pln_dfs 
           to multiline windows"""
        col = self.window["-r5_txt_00-"].get()
        name = self._get_activated_member()
        if col not in self.pln_dfs[name].columns.values.tolist():
            self.pln_dfs[name][col] = ""
        for i, txt in enumerate(self.pln_dfs[name][col]):
            self.window[f"-r5_mul_{i:02d}-"].update(txt)


    def r5_df_from_multiline(self, eid):
        """contents in multiline window is copied to dataframe
        Args:
            eid (int): multiline itme id
        """
        name = self._get_activated_member()
        if name != self.param["user_name"]:
            return
        indices = ["month", "week1", "week2", "week3", "week4"]
        col = self.window["-r5_txt_00-"].get()
        self.pln_dfs[name].loc[indices[eid], col] = self.values[f"-r5_mul_{eid:02d}-"]

    def r5_arrow_button_pressed(self, eid):
        """change to the next month or previous month"""
        ym = self.window["-r5_txt_00-"].get()
        y = int(ym[:4])
        m = int(ym[5:7])
        
        eid = -1 if eid == 0 else eid
        m += eid
        if m == 0:
            y -= 1
            m = 12
        if m == 13:
            y += 1
            m = 1
        self.window["-r5_txt_00-"].update(f"{y:04d}-{m:02d}")

        self._r5_multiline_from_df()

# ==========================================================================
# internal use functions
#===========================================================================
    # read write =======================================================================
    def _read_prj_file(self):
        """ 
         reading each member's prj file
        self.prj_dfs (project dataframes) is dictionary
        {keys are member name : values are each member's dataframe}
         If prj file is not exist, create new dataframe. 
        it has initial tickets ("one off work" and "regularly work")
         After read all prj files, create dictionaries "dic_prj1_2" and "dic_prj_task"
        "dic_prj1_2" -> key is project 1, values are project 2 
        "dic_prj1_task" -> key is combined project1 and project 2, values are task. 
        these dictionaries are used for checking input box of r1 (ticket create) and creating self.prj
        """
        self.prj_dfs = {}
        for name in self.param["team_members"]:
            file_name = self.prj_file.replace("--name--", name)
            if os.path.isfile(file_name):
                self.prj_dfs[name] = pd.read_pickle(file_name)
                continue
            items = []
            items.append(["Other", "One-off", "1", "One off work", "", False, "", "", 2, 2, name, "", "", self.param["status"][0], "", "", 0, "", "", 0, "6a1a57"])
            items.append(["Other", "Regularly", "1", "Regularly work", "", False, "", "", 2, 2, name, "", "", self.param["status"][0], "", "", 0, "", "", 0, "783993"])
            indices = [self._str_to_hash_id(item, self.param["columns"]) for item in items]
            self.prj_dfs[name] = pd.DataFrame(items, columns=self.param["columns"], index=indices)

        # get project 1&2 title for check box and check new ticktet
        self.dic_prj1_2 = defaultdict(set)
        self.dic_prj_task = defaultdict(set)
        for df in self.prj_dfs.values():
            for item in df.itertuples(name=None):
                prj = "-".join(item[1:3])
                self.dic_prj1_2[item[1]].add(item[2])
                self.dic_prj_task[prj].add(item[3])
        self.prj = sorted(list(self.dic_prj_task.keys()))


    def _save_prj_file(self):
        file_name = self.prj_file.replace("--name--", self.param["user_name"])
        self.prj_dfs[self.param["user_name"]].to_pickle(file_name)


    def _read_daily_schedule_file(self):
        self.sch_dfs = {}
        for name in self.param["team_members"]:
            file_name = self.sch_file.replace("--name--", name)
            if os.path.isfile(file_name):
                self.sch_dfs[name] = pd.read_pickle(file_name)
            else:
                indices = [f"{i//4:02d}:{15*(i%4):02d}" for i in range(24*4)] + self.param["schedule_add_info"]
                self.sch_dfs[name] = pd.DataFrame(columns=[], index=indices)


    def _save_daily_schedule_file(self):
        file_name = self.sch_file.replace("--name--", self.param["user_name"])
        dir_path, _ = os.path.split(file_name)
        if not os.path.isdir(dir_path):
            ret = sg.popup_ok_cancel(f"{dir_path} is not exist. Create this directory(ies) ?")
            if ret != "OK":
                return
            os.makedirs(dir_path) 
        self.sch_dfs[self.param["user_name"]].to_pickle(file_name)


    def _read_man_hour_tracker_file(self):
        self.trk_dfs = {}
        for name in self.param["team_members"]:
            file_name = self.trk_file.replace("--name--", name)
            if os.path.isfile(file_name):
                self.trk_dfs[name] = pd.read_pickle(file_name)
            else:
                indices = self.prj_dfs[self.param["user_name"]].index.values.tolist()
                self.trk_dfs[name] = pd.DataFrame(columns=[], index=indices)


    def _save_man_hour_traker_file(self):
        file_name = self.trk_file.replace("--name--", self.param["user_name"])
        dir_path, _ = os.path.split(file_name)
        if not os.path.isdir(dir_path):
            ret = sg.popup_ok_cancel(f"{dir_path} is not exist. Create this directory(ies) ?")
            if ret != "OK":
                return
            os.makedirs(dir_path)
        self.trk_dfs[self.param["user_name"]].to_pickle(file_name)


    def _read_monthly_plan_file(self):
        self.pln_dfs = {}
        for name in self.param["team_members"]:
            file_name = self.pln_file.replace("--name--", name)
            if os.path.isfile(file_name):
                self.pln_dfs[name] = pd.read_pickle(file_name)
            else:
                indices = ["month", "week1", "week2", "week3", "week4"]
                self.pln_dfs[name] = pd.DataFrame(columns=[], index=indices)


    def _save_monthly_plan_file(self):
        file_name = self.pln_file.replace("--name--", self.param["user_name"])
        dir_path, _ = os.path.split(file_name)
        if not os.path.isdir(dir_path):
            ret = sg.popup_ok_cancel(f"{dir_path} is not exist. Create this directory(ies) ?")
            if ret != "OK":
                return
            os.makedirs(dir_path)
        self.pln_dfs[self.param["user_name"]].to_pickle(file_name)


    # calculation =======================================================================
    def _calc_ticket_position(self, user):
        """
        calculating coordinate of the tickets which is in self.sch_dfs[user] 
        and own status is not "Done"

        Args:
            user (str): selected user name
        """
        tmp_df = self.prj_dfs[user].copy()
        tmp_df = tmp_df[tmp_df["Status"] != "Done"]
        tmp_df["begin_pos"] = 0
        tmp_df["end_pos"] = 0
        tmp_df["prj"] = tmp_df["Project1"] + "-" + tmp_df["Project2"]
        tmp_df = tmp_df.sort_values("Priority")

        time_to_pix = 100 / self.param["hour_in_date"]
        begin_idx = tmp_df.columns.get_loc('begin_pos')
        end_idx = tmp_df.columns.get_loc('end_pos')
        flag_cal_regularly = False
        for i, (es_time, prj12) in enumerate(zip(tmp_df["Update_Estimation"], tmp_df["prj"])):
            if prj12 == "Other-Regularly":
                reg_start_id = i
                flag_cal_regularly = True
                break
            if i:
                tmp_df.iloc[i, begin_idx] = tmp_df.iloc[i-1, end_idx]
                tmp_df.iloc[i, end_idx] = tmp_df.iloc[i, begin_idx] + es_time * time_to_pix
                continue
            tmp_df.iloc[i, begin_idx] = 0
            tmp_df.iloc[i, end_idx] = es_time * time_to_pix

        # "Other-Regularly" coordinates are calculated independently of other tickets
        if flag_cal_regularly:
            ue_idx = tmp_df.columns.get_loc('Update_Estimation')
            for i, es_time in enumerate(tmp_df.iloc[reg_start_id:,ue_idx]):
                row = reg_start_id + i
                if i:
                    tmp_df.iloc[row, begin_idx] = tmp_df.iloc[row-1, end_idx]
                    tmp_df.iloc[row, end_idx] = tmp_df.iloc[row, begin_idx] + es_time * time_to_pix
                    continue
                tmp_df.iloc[row, begin_idx] = 0
                tmp_df.iloc[row, end_idx] = es_time * time_to_pix

        self.ticket_pos_df = tmp_df.copy()


    # def _create_id(self, str):
    #     return hashlib.md5(str.encode()).hexdigest()

    def _str_to_hash_id(self, item, titles):
        """
        ticket id is generated with hash function from project1, 2, task, ticket and in charge
        """
        item_ids = [i for i, title in enumerate(titles) if title in self.param["hash_item"]]
        x = "-".join([item[i] for i in item_ids])
        return hashlib.md5(x.encode()).hexdigest()


    def _define_ticket_color(self, project1, project2, task, ds=None):
        if ds:
            project1 = ds["Project1"]
            project2 = ds["Project2"]
            task = ds["Task"]
        x = "-".join([project1, project2, task])
        x = hashlib.md5(x.encode()).hexdigest()
        c = [w for w in x if w in "0123456789a"]
        return "".join(["#"] + c[:min(len(c),6)] + ["a"]*max(6-len(c), 0))


    def _priority_update(self, ticket_id=None, step=0, name=None):
        """update priorities of tickets

        Args:
            ticket_id (str, optional): selected tieckt id. Defaults to None.
            step (int, optional): priority up down value. Defaults to 0.
            name (str, optional): selected member name. Defaults to None.
            for drawing l1 chart, can update priorites of other member. but cannot save.
        """
        name = name if name else self.param["user_name"]

        if ticket_id and step:
            pri_df = self.prj_dfs[name]["Priority"].copy()
            new_pri = pri_df[ticket_id] + step
            pri_df[pri_df >= new_pri] += 1
            pri_df[ticket_id] = new_pri
            self.prj_dfs[name]["Priority"] = pri_df

        # initialize
        # default 0 is high priority (maximum value + 1)
        pri_df = self.prj_dfs[name]["Priority"].copy()
        pri_df[self.prj_dfs[name]["Priority"]==0] = pri_df.max() + 1
        indices = self.prj_dfs[name].query("Project1 == 'Other' & Project2 == 'Regularly'").index.values
        # tickets which is in "Other-Regulary" or status of which is "Done" ticket is calculated independently
        pri_df.loc[indices] += 9999
        pri_df[self.prj_dfs[name]["Status"]==self.param["status"][3]] += 99999
        self.prj_dfs[name]["Priority"] = pri_df
        # sort 
        self.prj_dfs[name] = self.prj_dfs[name].sort_values("Priority")
        # re arrange
        self.prj_dfs[name]["Priority"] = [i+1 for i in range(self.prj_dfs[name].shape[0])]


    def _get_activated_member(self):
        return [name for i, name in enumerate(self.param["team_members"]) if self.values[f"-hd_rdi_{i:02d}-"]][0]
        

    def _get_series_from_ticket_id(self, ticket_id):
        for df in self.prj_dfs.values():
            if ticket_id in df.index.values.tolist():
                return True, df.loc[ticket_id]
        return False, ""


    def _update_sch_dfs(self, ticket_id):
        """
        scheduling ticket to daily schedule
        self.sch_dfs[user].loc[row, col] value is set ticket_id.
        then "row" is time band which is calculated form selected r2 table rows.
        "col" is day displayed top of r2 daily tab

        Args:
            ticket_id (str): selected ticket id

        Returns:
            bool: True means r2 some rows of r2 table is selected 
        """
        sch_col = self.window["-r2_txt_02-"].get()
        sch_row = self.values["-r2_tbl_00-"]
        user_name = self.param["user_name"]
        if not sch_row:
            return False
        if sch_col not in self.sch_dfs[user_name].columns.values.tolist():
            self.sch_dfs[user_name][sch_col] = ""
        sch_row = [row + self.param["daily_begin"]*4 for row in sch_row]
        indices = [f"{(i)//4:02d}:{15*((i)%4):02d}" for i in sch_row]
        self.sch_dfs[user_name].loc[indices, sch_col] = ticket_id
        return True
        
    
    def _warning_not_done_track_record(self):
        """
        If there is a difference between the contents of sch dataframe and trk dataframe
        before today, a warning will be displayed. 
        it is intended to prevent forgetting record
        """
        trk_user = self.trk_dfs[self.param["user_name"]]
        sch_user = self.sch_dfs[self.param["user_name"]]
        sch_user = sch_user.iloc[:24*4,:]

        trk_sum = trk_user.sum()
        sch_sum = sch_user[sch_user != ""].count() * 0.25

        com_df = pd.concat([trk_sum, sch_sum], axis=1, keys=["trk", "sch"])
        not_entered_days = com_df[com_df["trk"] != com_df["sch"]].index.values.tolist()
        
        not_entered_days = [d for d in not_entered_days if datetime.date(*list(map(int, d.split("/")))) < datetime.date.today()]

        if not_entered_days:
            for not_entered_day in not_entered_days:
                sg.popup_ok(f"Record of below date is not submitted \r\n{not_entered_day}")


    def get_reason_of_over_estimation_tickets(self, ticket_ids=None, shorter=False):
        """compare the man hour record and working date with estimation and due date.
           if over the estimation, save the reason to "Comment" of prj_df after get a reason by popup window 

        Args:
            ticket_ids (list, optional): tickets in ticket_ids are checked over estimation. Defaults to None.
            shorter (bool, optional): if true, ask the reason why man hour is shorter than estimaion also. Defaults to False.
        """
        name = self.param["user_name"]
        if not ticket_ids:
            ticket_ids = self.prj_dfs[name].index.values.tolist()
        for ticket_id in ticket_ids:
            if self.prj_dfs[name].loc[ticket_id, "Project1"] + "-" + self.prj_dfs[name].loc[ticket_id, "Project2"] == "Other-Regularly":
                continue
            est_hour = self.prj_dfs[name].loc[ticket_id, "Update_Estimation"]
            reg_hour = self.prj_dfs[name].loc[ticket_id, "Man_hour_reg"]
            due_date = self.prj_dfs[name].loc[ticket_id, "Due_date"]
            reg_date = self.prj_dfs[name].loc[ticket_id, "End_date_reg"]
            # check due date
            flags_over = [0, 0, 0]
            try:
                due_date = datetime.datetime.strptime(due_date, r"%Y/%m/%d")
                reg_date = datetime.datetime.strptime(reg_date, r"%Y/%m/%d")
                flags_over[0] = 1 if due_date < reg_date else 0
            except:
                flags_over[0] = 0

            # check estimation hour
            if est_hour * 1.2 < reg_hour:
                flags_over[1] = 1
            if reg_hour < est_hour * 0.8 and shorter:
                flags_over[2] = 1

            if sum(flags_over) == 0:
                continue

            # get reason
            ticket_ds = self.prj_dfs[name].loc[ticket_id]
            msg = [f"Please input reason !!"]
            msg += [f"project1&2  : {'-'.join([ticket_ds['Project1'], ticket_ds['Project2']])}"]
            msg += [f"task-ticket : {'-'.join([ticket_ds['Task'], ticket_ds['Ticket']])}"]
            tmp = [f"due date   : {due_date}, result date : {reg_date}"]
            tmp += [f"estimation : {est_hour}, result hour : {reg_hour}"]
            tmp += [f"estimation : {est_hour}, result hour : {reg_hour}"]
            msg += [m for m, f in zip(tmp, flags_over) if f]
            msg += ["Please Don't press Cancel button"]
            msg = "\r\n".join(msg)
            reason_txt = False
            reason_txt = sg.popup_get_text(message=msg, title="Please input reason", default_text=self.prj_dfs[name].loc[ticket_id, "Comment"], )
            print("reason", reason_txt)
            if reason_txt:
                self.prj_dfs[name].loc[ticket_id, "Comment"] = reason_txt