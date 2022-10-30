# %% =======================================================================
# import libraries
#===========================================================================
import os
import datetime

import pandas as pd
import PySimpleGUI as sg  

# %% =======================================================================
# class
#===========================================================================
class ScheduleManageLayout:

    """
    create pysimple gui layout object.
    methods are
        _layout()
            + _header_layout()
            + _left_tab_layout()
                + l1_layout()
                + l2 ...
            + _right_tab_layout()
                + r1_layout()
                + r2 ...
            + _bind_items()
    """

    def _layout(self):

        hd = self._header_layout()
        lt = self._left_tab_layout()
        rt = self._right_tab_layout()

        # All the stuff inside your window.
        layout = [[hd, lt + rt]]
        # layout = [[hd, *rt, lt]]
        return layout

    # %% =======================================================================
    # header
    #===========================================================================
    def _header_layout(self):

        # project check box
        self.hd_cbx_names = [p for p in self.prj]
        cbx_list = [[name, True, f"-hd_cbx_{i:02d}-"] for i, name in enumerate(self.prj)]
        self.hd_cbx = [sg.Checkbox(text=name, default=tf, key=key, size=(self.sizes.header_chk_box_w, self.sizes.header_chk_box_h), p=0, enable_events=True) for name, tf, key in cbx_list]

        # member radio button
        rdi_list = [[name, name==self.params.user_name, f"-hd_rdi_{i:02d}-"] for i, name, in enumerate(self.params.team_members)]
        hd_rdi = [sg.Radio(name, group_id="hd_rdi", default=tf, key=key, size=(self.sizes.header_radio_w, self.sizes.header_radio_h), p=0, enable_events=True) for name, tf, key in rdi_list]

        # button
        btn_list = ["All", "Clear", "Refresh", "Upload", "Reload"]
        hd_btn = [sg.Button(name, key=f"-hd_btn_{i:02d}-", size=(self.sizes.header_button_w, self.sizes.header_button_h)) for i, name in enumerate(btn_list)]
        hd_txt = [sg.Text("", key="-hd_txt_00-", size=(self.sizes.header_button_w, self.sizes.header_button_h), justification="center")]
        # columns
        nc = self.params.header_num_row
        hd_cl1 = [sg.Column([[cb for cb in self.hd_cbx[i::nc]] for i in range(nc)], size=(self.sizes.header_clm_chk_w, self.sizes.header_clm_chk_h))]
        hd_cl2 = [sg.Column([[btn] for btn in hd_btn[0:3]], vertical_alignment="center", size=(self.sizes.header_clm_btn_w, self.sizes.header_clm_btn_h))]
        hd_cl3 = [sg.Column([[btn] for btn in hd_btn[3:5]] + [hd_txt], vertical_alignment="center", size=(self.sizes.header_clm_btn_w, self.sizes.header_clm_btn_h))]
        hd_cl4 = [sg.Column([[rd for rd in hd_rdi[i::nc]] for i in range(nc)], size=(self.sizes.header_clm_rdi_w, self.sizes.header_clm_rdi_h))]

        # header layout
        hd = [hd_cl1 + hd_cl2 + hd_cl3 + hd_cl4]
        return hd

    # %% =======================================================================
    # left tab
    #===========================================================================
    def _left_tab_layout(self):

        l1 = self._l1_layout()
        l2 = self._l2_layout()
        l3 = self._l3_layout()
        l4 = self._l4_layout()
        l5 = self._l5_layout()
        # l0 = self._l0_layout()

        # tab group
        lt = [sg.TabGroup([l1, l2, l3, l4, l5], size=(self.sizes.left_tab_group_w, self.sizes.left_tab_group_h), enable_events=True, key="-lt_grp_00-")]
        
        return lt


    def _l1_layout(self):

        gbl = (0, 0)
        gtr = (self.sizes.graph_top_right_w, self.sizes.graph_top_right_h)

        # graph for calendar
        self.l1_grp_cal = sg.Graph((self.sizes.left_tab1_canvas_w,10), gbl, gtr, pad=0)
        self.l1_grp_cal2 = sg.Graph((self.sizes.often_width, 10), gbl, gtr, pad=0)
        self.l1_frm_cal = [[sg.Frame("", [[self.l1_grp_cal2, self.l1_grp_cal]], border_width=0)]]

        # graph for schedule
        grp_r_click_menu = ["menu", ["Scheduling_", "Edit_"] + [f"{s}_" for s in self.params.status] + ["Follow_up_"]]
        self.l1_grp = [sg.Graph((self.sizes.left_tab1_canvas_w, self.sizes.left_tab1_canvas_h), gbl, gtr, pad=0, background_color=self.theme.graph_background, key=f"-l1_grp_{i:02d}-", right_click_menu=grp_r_click_menu, enable_events=True) for i in range(len(self.prj))]
        self.l1_grp2 = [sg.Graph((self.sizes.often_width, self.sizes.left_tab1_canvas_h), gbl, gtr, pad=0, background_color=self.theme.graph_background, key=f"-l1_grp2_{i:02d}-", right_click_menu=grp_r_click_menu, enable_events=True) for i in range(len(self.prj))]
        self.l1_frm = [[sg.Frame(p, [[g2, g]], key=f"-l1_frm_{i:02d}-", border_width=0)] for i, (p, g, g2) in enumerate(zip(self.prj, self.l1_grp, self.l1_grp2))]
        self.l1_clm = [sg.Column(self.l1_frm_cal + self.l1_frm, scrollable=True, vertical_scroll_only=False, size=(self.sizes.left_tab_group_w, self.sizes.left_tab_group_h))]

        l1 = [sg.Tab("Project", [self.l1_clm], key="-l1_tbg_00-")]
        return l1


    def _l2_layout(self):

        # tab2 - status
        l2_tx1 = [sg.Text("Left box work in progress")]

        l2 = [sg.Tab("Status", [l2_tx1], key="-l2_tbg_00-")]
        return l2


    def _l3_layout(self):

        l3_tx1 = [sg.Text("You are able to update only your ticket priority")]
        l3_tx2 = [sg.Text("priority up down buttons")]

        cbx_list = [[name, name!="Done", f"-l3_cbx_{i:02d}-"] for i, name in enumerate(self.params.status)]
        self.l3_cbx = [sg.Checkbox(text=name, default=tf, key=key, size=(self.sizes.header_chk_box_w, self.sizes.header_chk_box_h), p=0, enable_events=True) for name, tf, key in cbx_list]

        grp_r_click_menu = ["menu", ["Scheduling_", "Edit_"] + [f"{s}_" for s in self.params.status]]
        tbl_tmp = [""] * len(self.params.priority_list)
        l3_tbl = [sg.Table(tbl_tmp, headings=self.params.priority_list, auto_size_columns=False, def_col_width=self.sizes.left3_col_width_w, row_height=self.sizes.tbl_row_hight, num_rows=70, vertical_scroll_only=False, justification="center", enable_events=True, right_click_menu=grp_r_click_menu, text_color=self.theme.text_table, background_color=self.theme.table_background, key="-l3_tbl_00-")]

        # button
        btn_list = ["⏫", "🔼", "🔽", "⏬", "🖥"]
        l3_btn = [sg.Button(name, key=f"-l3_btn_{i:02d}-", size=(self.sizes.header_button_w, self.sizes.header_button_h)) for i, name in enumerate(btn_list)]
        l3_cbx2 = [sg.Checkbox(text="Auto activate", default=self.params.auto_priority_activate, key="-l3_cbx_20-")]
        l3_col = l3_btn + l3_cbx2

        l3_inp1 = [sg.Text("query", size=(5,1)), sg.Input("", key="-l3_inp_00-", size=(80, 5)), sg.Text('input 1st arg of df.query() like Project1 == "TEST" and Status in ("ToDo", "Done")', size=(80,1), key="-l3_txt_00-")]
        l3_inp2 = [sg.Text("sort", size=(5,1)), sg.Input("", key="-l3_inp_01-", size=(80, 5)), sg.Text('input sort item(s) like "Man_hour_reg", "End_date_reg"', size=(80,1), key="-l3_txt_01-")]
        l3_btn2 = [sg.Button("Display", key="-l3_btn_20-", size=(self.sizes.header_button_w, self.sizes.header_button_h))]

        l3 = [sg.Tab("Table", [l3_tx1, l3_col, l3_inp1, l3_inp2, l3_btn2, l3_tbl], key="-l3_tbg_00-")]
        return l3


    def _l4_layout(self):

        btn_list = ["Accept", "Deny"]
        l4_btn = [sg.Button(name, key=f"-l4_btn_{i:02d}-", size=(self.sizes.header_button_w, self.sizes.header_button_h)) for i, name in enumerate(btn_list)]

        tbl_tmp = [["", "", "", "", "", "", ""]] * 100
        tbl_headings = ["From", "To", "Project1", "Project2", "Task", "Ticket", "Due_date"]
        col_width = [12, 12, 20, 20, 20, 20, 15]
        l4_tbl = [sg.Table(tbl_tmp, headings=tbl_headings, auto_size_columns=False, col_widths=col_width, row_height=self.sizes.tbl_row_hight, num_rows=40, justification="center", enable_events=False, text_color=self.theme.text_table, background_color=self.theme.table_background, key="-l4_tbl_00-")]
        
        l4 = [sg.Tab("Order", [l4_btn, l4_tbl], key="-l4_tbg_00-")]
        return l4

    def _l5_layout(self):
        

        btn_list = ["Remove"]
        l5_btn = [sg.Button(name, key=f"-l5_btn_{i:02d}-", size=(self.sizes.header_button_w, self.sizes.header_button_h)) for i, name in enumerate(btn_list)]

        tbl_tmp = [["", "", "", "", "", "", "", ""]] * 100
        tbl_headings = ["Index", "Project1", "Project2", "Task", "Ticket", "Due_date", "In_charge", "Status"]
        col_width = [30, 15, 15, 15, 30, 12, 12, 15]
        l5_tbl = [sg.Table(tbl_tmp, headings=tbl_headings, auto_size_columns=False, col_widths=col_width, row_height=self.sizes.tbl_row_hight, num_rows=300, justification="center", enable_events=False, text_color=self.theme.text_table, background_color=self.theme.table_background, key="-l5_tbl_00-")]
        l5_txt = [sg.Text("", key="-l5_txt_00-", size=(sum(col_width), 3))]
        
        l5 = [sg.Tab("follow", [l5_txt, l5_btn, l5_tbl], key="-l5_tbg_00-")]
        return l5
        

    def _l0_layout(self):

        l0_tx1 = [sg.Text("Setting Tab")]
        l0_btn = [sg.Button("Save & Restart", key="-l0_btn_00-", size=(self.sizes.header_button_w, self.sizes.header_button_h))]
        
        l0_SET = []
        for setting, input_type in zip(self.SETTINGS_DIR, self.SETTINGS_DIR_TYPE):
            l0_SET.append([sg.Text(setting, size=(self.sizes.header_chk_box_w, self.sizes.header_chk_box_h))] + [sg.Input(self.df_settings.loc[setting, i+1], key=f"-{setting}_{i:02d}-", size=(self.sizes.right_input_w, self.sizes.right_input_h)) for i, _ in enumerate(input_type)])
        for setting, input_type in zip(self.SETTINGS_PARAM, self.SETTINGS_PARAM_TYPE):
            l0_SET.append([sg.Text(setting, size=(self.sizes.header_chk_box_w, self.sizes.header_chk_box_h))] + [sg.Input(self.df_settings.loc[setting, i+1], key=f"-{setting}_{i:02d}-", size=(self.sizes.right_input_w, self.sizes.right_input_h)) for i, _ in enumerate(input_type)])
        for setting, input_type in zip(self.SETTINGS_SIZE, self.SETTINGS_SIZE_TYPE):
            l0_SET.append([sg.Text(setting, size=(self.sizes.header_chk_box_w, self.sizes.header_chk_box_h))] + [sg.Input(self.df_settings.loc[setting, i+1], key=f"-{setting}_{i:02d}-", size=(self.sizes.right_input_w, self.sizes.right_input_h)) for i, _ in enumerate(input_type)])

        l0 = [sg.Tab("Settings", [l0_tx1, l0_btn] + l0_SET)]
        return l0





    # %% =======================================================================
    # right tab
    #===========================================================================
    def _right_tab_layout(self):

        r1 = self._r1_layout()
        r2 = self._r2_layout()
        r3 = self._r3_layout()
        r4 = self._r4_layout()
        r5 = self._r5_layout()
        r6 = self._r6_layout()
        r7 = self._r7_layout()
        r8 = self._r8_layout()

        rt = [sg.TabGroup([r1, r2, r3, r4, r5, r6, r7, r8], size=(self.sizes.right_tab_group_w, self.sizes.right_tab_group_h), enable_events=True, key="-rt_grp_00-")]
        return rt


    def _r1_layout(self):

        # button
        btn_list = ["Create", "Update", "Delete"]
        r1_btn = [sg.Button(name, key=f"-r1_btn_{i:02d}-", size=(self.sizes.right_button_w, self.sizes.right_button_h)) for i, name in enumerate(btn_list)]
        
        # texts
        txt_list = ["Project-1", "Project-2", "Task", "Ticket"]
        txt_list += ["Ready Date", "Due Date", "Estimation", "Estimation(additional)"]
        txt_list += ["In charge", "       Status", "File", "Details", "Comment"]
        txt_list += ["Precious task", "Next task"]
        r1_txt = [sg.Text(t, size=(self.sizes.right_input_w, self.sizes.right_input_h), justification="left", pad=0) for t in txt_list]

        # input boxes
        inp_d = [""] * 11
        inp_d[4] = datetime.datetime.strftime(datetime.date.today(), r"%Y/%m/%d")
        inp_d[7] = 0
        inp_s = [(self.sizes.right_input_w, self.sizes.right_input_h)] * 8 + [(self.sizes.right_input_w * 4, self.sizes.right_input_h)] * 3
        self.r1_inp = [sg.Input(d, size=s, pad=0, key=f"-r1_inp_{i:02d}-", enable_events=True) for i, (d, s) in enumerate(zip(inp_d, inp_s))]

        # combo boxes
        r1_cmb = [sg.Combo(self.params.team_members + ["Assign to all"], default_value=self.params.user_name, size=(self.sizes.right_input_w, self.sizes.right_input_h), key="-r1_cmb_00-")]
        r1_cmb += [sg.Combo(self.params.status, default_value=self.params.status[0], size=(self.sizes.right_input_w, self.sizes.right_input_h), key="-r1_cmb_01-")]

        # project check box
        cbx_list = ["Edit mode"]
        cbx_list = [[name, False, f"-r1_cbx_{i:02d}-"] for i, name in enumerate(cbx_list)]
        r1_cbx = [sg.Checkbox(text=name, default=tf, key=key, size=(self.sizes.header_chk_box_w, self.sizes.header_chk_box_h), enable_events=False) for name, tf, key in cbx_list]

        layout = [r1_btn, 
                  r1_txt[0:4], self.r1_inp[0:4],
                  r1_txt[4:8], self.r1_inp[4:8],
                  r1_txt[8:10], r1_cmb[0:2], 
                  r1_txt[10:11], self.r1_inp[8:9], 
                  r1_txt[11:12], self.r1_inp[9:10], 
                  r1_txt[12:13], self.r1_inp[10:11], 
                  r1_cbx]
        r1_clm = [sg.Column(layout)]

        r1_txt1 = [sg.Text("➡ 🎫 ➡")]
        r1_txt2 = [sg.Text("Previous")]
        r1_txt3 = [sg.Text("Next")]
        r1_tbl2 = [sg.Table([["Tickets"]], auto_size_columns=False, def_col_width=self.sizes.r1_table_width, row_height=self.sizes.tbl_row_hight, num_rows=40, vertical_scroll_only=True, justification="left", enable_events=False, text_color=self.theme.text_table, background_color=self.theme.table_background, key="-r1_tbl_02-")]
        r1_tbl3 = [sg.Table([["Tickets"]], auto_size_columns=False, def_col_width=self.sizes.r1_table_width, row_height=self.sizes.tbl_row_hight, num_rows=40, vertical_scroll_only=True, justification="left", enable_events=False, text_color=self.theme.text_table, background_color=self.theme.table_background, key="-r1_tbl_03-")]
        r1_clm2 = [sg.Column([r1_txt2, r1_tbl2])]
        r1_clm3 = [sg.Column([r1_txt3, r1_tbl3])]
        r1_clm1 = [sg.Column([r1_clm2 + r1_txt1 + r1_clm3])]
        r1_txt4 = [sg.Text("", key="-r1_txt_04-")]

        r1 = [sg.Tab("planing", [r1_clm, r1_clm1, r1_txt4], key="r1")]
        return r1


    def _r2_layout(self):

        r2_txt1 = [sg.Text("", size=(self.sizes.right_input_w, self.sizes.right_input_h), p=0, justification="center", key="-r2_txt_00-"), sg.Text("     Begin   ~    End    (Total)   <Break>", p=0)]
        r2_txt2 = [sg.Text(datetime.date.today().strftime(r"%Y/%m/%d"), size=(self.sizes.right_input_w, self.sizes.right_input_h), p=0, justification="center", enable_events=True, key="-r2_txt_02-"), sg.Text("     00:00   ~   00:00   (00:00)   <00:00>", p=0, key="-r2_txt_03-")]

        btn_list = ["", "💾 Record", "📨🤛", "👉📨", "delete"]
        r2_btn = [sg.Button(name, key=f"-r2_btn_{i:02d}-", size=(int(self.sizes.header_button_w*1.2), self.sizes.header_button_h)) for i, name in enumerate(btn_list)]
        r2_btn1 = [sg.Button("◀︎", size=(2,1), key="-r2_btn_10-")] + [sg.Button("●", size=(2,1), key="-r2_btn_11-")] + [sg.Button("▶︎", size=(2,1), key="-r2_btn_12-")]

        tbl_tmp = [["", "", ""]] * self.params.daily_table_rows
        tbl_headings = ["Daily Schedule","time","Outlook"]
        r2_table_width = [self.sizes.r2_table_width_1, self.sizes.r2_table_width_2, self.sizes.r2_table_width_3]
        r2_tbl = [sg.Table(tbl_tmp, headings=tbl_headings, auto_size_columns=False, col_widths=r2_table_width, row_height=self.sizes.tbl_row_hight, justification="center", enable_events=False, text_color=self.theme.text_table, num_rows=self.params.daily_table_rows, vertical_scroll_only=True, hide_vertical_scroll=True, background_color=self.theme.table_background, expand_y=True, key="-r2_tbl_00-")]
        r2_col1 = [sg.Column([r2_tbl], scrollable=True, vertical_scroll_only=True, size=(self.sizes.right_comment_boxes_w, self.sizes.right_comment_boxes_h*6))]
        r2_cbx = [sg.Checkbox(text="activate left click", default=False, p=0, key="-r2_cbx_00-")]

        r2_inp = [[sg.Text(t, size=(self.sizes.right_input_w, self.sizes.right_input_h), p=0, justification="left"), sg.Input("", size=(self.sizes.right_input_w * 4, self.sizes.right_input_h), p=0, enable_events=True, key=f"-r2_inp_{i:02d}-")] for i, t in enumerate(self.params.schedule_add_info[1:])]
        r2_col2 = [sg.Column(r2_inp, scrollable=True, size=(self.sizes.right_comment_boxes_w, self.sizes.right_comment_boxes_h), vertical_scroll_only=True)]

        r2 = [sg.Tab("Daily", [r2_txt1, r2_txt2, r2_btn1+r2_btn[1:4], r2_col1, r2_btn[4:]+r2_cbx, r2_col2], key="r2")]
        return r2


    def _r3_layout(self):

        btn_list = ["📨", "🗂", "🗒"]
        r3_btn = [sg.Button(name, key=f"-r3_btn_{i:02d}-", size=(int(self.sizes.header_button_w*1.2),self.sizes.header_button_h)) for i, name in enumerate(btn_list)]

        r3_txt1 = [sg.Text("working hour")]
        r3_inp1 = [sg.Multiline("", size=(self.sizes.right_team_box_w, self.sizes.right_team_box_h), key="-r3_mul_00-")]
        r3_txt2 = [sg.Text("information")]
        r3_inp2 = [sg.Multiline("", size=(self.sizes.right_team_box_w, self.sizes.right_team_box_h), key="-r3_mul_01-")]

        r3 = [sg.Tab("team", [r3_btn, r3_txt1, r3_inp1, r3_txt2, r3_inp2], key="r3")]
        return r3


    def _r4_layout(self):

        r4_tx1 = [sg.Text("Right box fever chart")]

        r4 = [sg.Tab("fever", [r4_tx1], key="r4")]
        return r4


    def _r5_layout(self):

        r5_btn0 = [sg.Button("◀︎", size=(2,1), key="-r5_btn_00-")]
        r5_btn1 = [sg.Button("▶︎", size=(2,1), key="-r5_btn_01-")]
        today = datetime.date.today()
        r5_txt = [sg.Text(f"{today.year:04d}-{today.month:02d}", key="-r5_txt_00-")]
        r5_upp = [r5_btn0 + r5_txt + r5_btn1]

        r5_low = [[sg.Text("Monthly Plan")]]
        r5_low += [[sg.Multiline("", size=(self.sizes.right_team_box_w, self.sizes.right_team_box_h), enable_events=True, key="-r5_mul_00-")]]
        r5_low += [[sg.Text("Weekly Plan")]]
        s = (self.sizes.right_team_box_w, self.sizes.right_team_box_h//8)
        r5_low += [[sg.Multiline("", size=s, enable_events=True, key=f"-r5_mul_{i:02d}-")] for i in range(1, 6)]
        r5_clm = [sg.Column(r5_low[2:], scrollable=True, vertical_scroll_only=True, size=(self.sizes.right_tab_group_w, self.sizes.right_tab_group_h))]

        r5 = [sg.Tab("Plan", r5_upp + r5_low[:2] + [r5_clm], key="r5")]
        return r5


    def _r6_layout(self):

        btn_list1 = ["Push", "Pull"]
        btn_list2 = ["🔼", "🔽", "Edit", "Add"]
        r6_btn1 = [sg.Button(name, key=f"-r6_btn1_{i:02d}-", size=(self.sizes.right_button_w, self.sizes.right_button_h)) for i, name in enumerate(btn_list1)]
        r6_btn2 = [sg.Button(name, key=f"-r6_btn2_{i:02d}-", size=(self.sizes.right_button_w, self.sizes.right_button_h)) for i, name in enumerate(btn_list2)]

        txt_list = ["Project-1", "Project-2", "Task"]
        r6_txt = [sg.Text(t, size=(self.sizes.right_input_w, self.sizes.right_input_h), justification="left", pad=0) for t in txt_list]
        self.r6_inp = [sg.Input("", size=(self.sizes.right_input_w, self.sizes.right_input_h), pad=0, key=f"-r6_inp_{i:02d}-", enable_events=True) for i in range(3)]

        tbl_tmp = [["", "", "", "", ""]] * 100
        tbl_headings = ["Ticket", "Estimation", "Record", "Ready Date", "Due Date"]
        r6_tbl = [sg.Table(tbl_tmp, headings=tbl_headings, auto_size_columns=False, col_widths=[16,8,8,12,12], row_height=self.sizes.tbl_row_hight, num_rows=20, justification="center", enable_events=False, text_color=self.theme.text_table, background_color=self.theme.table_background, key="-r6_tbl_00-")]
        
        r6_mul = [sg.Multiline("", size=(self.sizes.right_team_box_w, self.sizes.right_team_box_h), enable_events=True, key="-r6_mul_00-")]
        r6_txt1 = [sg.Text(" Ticket name ␣ estimation ␣ ready date ␣ due date", pad=0)]
        r6_txt2 = [sg.Text(' "-" is regarded None.', pad=0)]
        r6_txt3 = [sg.Text(" date should be yyyy/mm/dd.", pad=0)]

        r6 = [sg.Tab("Task", [r6_btn1, r6_txt, self.r6_inp, r6_tbl, r6_btn2[2:], r6_txt1, r6_txt2+r6_txt3, r6_mul], key="r6")]
        return r6


    def _r7_layout(self):

        s = (self.sizes.right_team_box_w * 2, self.sizes.right_team_box_h * 2)
        r7_mul = [sg.Multiline("", size=s, key="-r7_mul_00-", enable_events=True)]
        r7 = [sg.Tab("Memo", [r7_mul], key = "-r7")] 
        return r7

    def _r8_layout(self):
        
        r8_btn0 = [sg.Button("log0", size=(self.sizes.right_button_w, self.sizes.right_button_h), key="-r8_btn_00-")]
        r8_btn1 = [sg.Button("log1", size=(self.sizes.right_button_w, self.sizes.right_button_h), key="-r8_btn_01-")]
        r8_btn2 = [sg.Button("log2", size=(self.sizes.right_button_w, self.sizes.right_button_h), key="-r8_btn_02-")]
        r8_btn3 = [sg.Button("log3", size=(self.sizes.right_button_w, self.sizes.right_button_h), key="-r8_btn_03-")]
        s = (self.sizes.right_team_box_w * 2, self.sizes.right_team_box_h * 2)
        r8_txt = [sg.Text("", size=s, key="-r8_txt_00-", enable_events=True)]
        r8 = [sg.Tab("log", [r8_btn0 + r8_btn1 + r8_btn2 + r8_btn3, r8_txt], key = "-r8")] 
        return r8


    # %% =======================================================================
    # other
    #===========================================================================

    def _bind_items(self):

        # MV : mouse move
        # LC : left click
        # MC : mouse click

        for grp in self.l1_grp:
            grp.bind("<Motion>", "MV-")
            grp.bind("<ButtonPress>", "LC-")
        for grp in self.l1_grp2:
            grp.bind("<Motion>", "MV-")
            grp.bind("<ButtonPress>", "LC-")

        for i, inp in enumerate(self.r1_inp):
            if i in [4,5]:
                inp.bind("<ButtonPress>", "LC-")

        self.window.bind("<Control-s>", "Cs-")
        self.window.bind("<Control-r>", "Cr-")

        self.window["-r2_tbl_00-"].bind("<Button1-Motion>", "DR-")
        self.window["-r2_tbl_00-"].bind("<ButtonPress>", "BP-")
        self.window["-r2_tbl_00-"].bind("<ButtonRelease>", "BR-")