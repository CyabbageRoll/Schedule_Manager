# %% =======================================================================
# import libraries
#===========================================================================
# default
import os
import bisect
import hashlib
import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict 
from heapq import heapify, heappush, heappop


# pip or conda install
import pandas as pd
import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import popup_get_date

# user
from b01_schedule_class_layout import ScheduleManageLayout
from b02_schedule_class_io import ScheduleManageIO

from c01_func_priority_calculation import SortTickets

# %% =======================================================================
# class
#===========================================================================

class ScheduleManage(ScheduleManageLayout, ScheduleManageIO):

    def __init__(self, logger):

        self.log_msg = []
        self.logger = logger
        self.logger.info("ScheduleManage Class start init")
        self.setting_file = r"../sch_m_setting.json"
        self.memo_file = r"../personal_memo.json"
        self.prj_dfs = {}
        self.sch_dfs = {}
        self.trk_dfs = {}
        self.pln_dfs = {}
        self.order_dic = {}
        self.sizes = {}
        self.params = {}
        self.colors = {}
        self.hd_cbx_names = []
        self.personal_memo = {"follow" : [], "memo" : "", "set" : {"prj" : [], "table_query" : "", "table_sort" : ""}}
        self.previous_selected_ticket = None
        self.values = None
        self._initialize() 
        self.app_schedule = [""] * self.params.daily_table_rows
        self.task_updating_df = self.prj_dfs[self.params.user_name].iloc[:1]
        self.r2_table_click_start = []
        self.r1_ticket_connections = {"p":[], "n":[]}

    def log(self, log_type="info", msg=""):
        if log_type == "info":
            self.logger.info(msg)
        if log_type == "debug":
            self.logger.debug(msg)
        self.log_msg.append(msg)
        self.log_msg = self.log_msg[-10:]
        txt_msg = "\n".join(self.log_msg)
        print(txt_msg)
        self.window["-r8_txt_01-"].update(txt_msg)

    def _initialize(self):

        warning_msg = self._read_settings_file()
        if warning_msg:
            sg.popup_ok(warning_msg)
            self.logger.info(f"warning at initialize {warning_msg}")
        self.reload_files(popup=False)

    def create_original_sg_theme(self):

        theme = self.theme
        theme_name = 'OriginalTheme'
        sg.LOOK_AND_FEEL_TABLE[theme_name] = {
                                        'BACKGROUND': theme.background,
                                        'TEXT': theme.text,
                                        'INPUT': theme.input_box,
                                        'TEXT_INPUT': theme.text_input,
                                        'SCROLL': theme.scroll,
                                        'BUTTON': (theme.button_pressed, theme.button_normal),
                                        'PROGRESS': (theme.progress_1, theme.progress_2),
                                        'BORDER': theme.border, 
                                        'SLIDER_DEPTH': theme.slider_depth, 
                                        'PROGRESS_DEPTH': theme.progress_depth,
        }

        return theme_name

    def create_window(self):
        """create window and refresh tabs after belows
            1. bind the mouse control items. (window must be finalized before bind)
            2. warning message is shown if tracking till yesterday is not done
        """

        if self.theme.use_user_setting:
            sg.theme(self.create_original_sg_theme())
        else:
            sg.theme(self.params.window_theme)
        layout = self._layout()
        self.window = sg.Window('Schedule Manager v2022xxxx', layout, size=(self.sizes.window_w, self.sizes.window_h), font=(self.params.font, self.params.font_size), finalize=True, resizable=True)
        _, self.values = self.window.read(timeout=1)

        self._bind_items()
        self.update_tabs()
        self._warning_not_done_track_record()


    def update_tabs(self):

        self._priority_update()
        if self.values["-l3_cbx_20-"]:
            self.calculate_priority()
        self.l1_chart_draw()
        self.set_right_click_menu_of_prj12_task()
        self.r2_daily_schedule_update()
        self.display_information_in_r2()
        self.display_team_box()
        self.display_plans_on_multiline()
        self.display_memo_item_in_r7_multi()
        self.display_follow_up_tickets()
        self.display_order_list_in_l4()
        self.set_previous_inputs()


    def parse_event(self):
        """read event and return the which location, which item, which id.

        Returns:
            return belows but event is not defined by layout class, return None or 0
            str : event. one of window.read returns
            str : event location like hd (header), r1(right tab 1), l2(left tab 2)
            str : event item like btn(button), rdi(radio) etc...
            int : item id. defined in layout class
            if event is l1 or l3 right click menu
                return event, "l1", "grp-RC", ticket id
        """
        event, self.values = self.window.read(timeout=1000*60*10) # TODO : set in json file

        if not event:
            return event, None, None, 0
        if len(event) <= 2:
            return event, None, None, 0
        if event[-1] == "_":
            # right click menu of l1 graph or l3 table was clicked.
            return event, "l1", "grp-RC", self.previous_selected_ticket
        if event[-1] == ".":
            # right click menu of r1 input box was clicked
            return event, "r1", "right_menu", event[:4]
        if event[-1] == ">":
            # right click menu of r2 table was clicked
            return event, "r2", "right_menu", event[-5:-1]
        if event[-1] == ":":
            # right click menu of r1 table was clicked
            return event, "r1", "right_menu_tbl", event[7:11]
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
# functions
#===========================================================================

    def activate_all_header_buttons(self):
        for cbx in self.hd_cbx:
            cbx.update(value=True)


    def deactivate_all_header_buttons(self):
        for cbx in self.hd_cbx:
            cbx.update(value=False)


    def show_prj_boxes_as_chk_box(self, eids=[]):
        """
        when one or some of header project check boxes is updated,
        call this function. 
        l1 frame(s) is hided or unhidden depend on check box is True or False
        Args:
            eids (list, optional): [description]. Defaults to [].
        """
        if not eids:
            eids = [i for i in range(len(self.prj))]
        else:
            for eid in eids:
                if self.hd_cbx[eid].get():
                    self.personal_memo["set"]["prj"].append(self.prj[eid])
                    self.personal_memo["set"]["prj"] = list(set(self.personal_memo["set"]["prj"]))
                else:
                    if self.prj[eid] in self.personal_memo["set"]["prj"]:
                        self.personal_memo["set"]["prj"].remove(self.prj[eid])

        for eid in eids:
            if self.hd_cbx[eid].get():
                self.l1_frm[eid][0].unhide_row()
            else:
                self.l1_frm[eid][0].hide_row()

        

    def header_alert_update(self, flag, str):

        if flag:
            self.window["-hd_txt_00-"].update(value=str, background_color=self.theme.alert)
        else:
            if self.window["-hd_txt_00-"].get() == str:
               self.window["-hd_txt_00-"].update(value="", background_color=self.theme.background)
        return
        

    # l1 =======================================================================
    def schedule_ticket_to_daily_table(self):
        """in below condition, clicked item is scheduled in daily table
            - activate left click checkbox of r2 tab(daily tab) is activated
            - r2 tab(daily tab) is activated
            - activated member is same as user
            - ticket is defined in user dataframe
        """
        if not self.values["-r2_cbx_00-"]:
            return
        if self.values["-rt_grp_00-"] != "r2":
            print("daily tab is not activated")
            return
        if self._get_activated_member() != self.params.user_name:
            print("you can update only your schedule. Other user's daily table is shown now")
            return
        if self._update_sch_dfs(self.previous_selected_ticket):
            self.r2_daily_schedule_update()
        return
    

    def get_and_remain_mouse_on_ticket_id(self, item, eid):
        """get mouse xy coordinate in graph area which mouse is above 
        and display the detail of ticket on r1 tab. 
        Remain ticket id for use next other event like right click menu. 

        Args:
            item (str): object where mouse is
            eid (int): graph id which mouse is above
        """

        item = item.split("-")[0]

        if item == "grp":
            self.mouse_x = int(self.l1_grp[eid].user_bind_event.x / self.sizes.left_tab1_canvas_w * self.sizes.graph_top_right_w)
            self.mouse_y = int(self.l1_grp[eid].user_bind_event.y / self.sizes.left_tab1_canvas_h * self.sizes.graph_top_right_h)
            # self.graph_positions has each ticket start y coordinate
            pos_index = bisect.bisect_left(self.graph_positions_todo[eid], self.mouse_x)
            ticket_id = self.graph_ticket_ids_todo[eid][pos_index-1]

        if item == "grp2":
            self.mouse_x = int(self.l1_grp2[eid].user_bind_event.x / self.sizes.often_width * self.sizes.graph_top_right_w)
            self.mouse_y = int(self.l1_grp2[eid].user_bind_event.y / self.sizes.left_tab1_canvas_h * self.sizes.graph_top_right_h)
            # self.graph_positions has each ticket start y coordinate
            if len(self.graph_ticket_ids_often[eid]) == 0:
                return
            num_col = len(self.graph_ticket_ids_often[eid][0])
            col = int(self.mouse_x / self.sizes.graph_top_right_w * num_col - 1e-4)
            row = int(self.mouse_y / self.sizes.graph_top_right_h * 5 - 1e-4)
            ticket_id = self.graph_ticket_ids_often[eid][row][col]

        if not ticket_id:
            return
        self.previous_selected_ticket = ticket_id
        if self.values["-r1_cbx_00-"]:
            return

        return ticket_id


    def process_l1_right_click_menu(self, event, ticket_id):
        """
        Caution! used this method when "L3" right click menu is clicked also 

        Args:
            event (str): one of window read returns
            ticket_id (str): activated ticket id (hash-md5)
        """

        # get ticket information. if ticket is not exist with unexpected reason, "return"
        flag_is_ticket, mouse_on_prj = self._get_is_ticket_and_series_from_ticket_id(ticket_id)
        if not flag_is_ticket:
            return
        in_charge = mouse_on_prj["In_charge"]

        # Branch processing
        if event[:-1] in self.params.status:
            if event[:-1] == "Done":
                ret = self.get_reason_of_over_estimation_tickets(ticket_ids=[ticket_id], shorter=True)
                if not ret:
                    return
            self.prj_dfs[in_charge].loc[ticket_id, "Status"] = event[:-1]

        r_menu = ["Scheduling_", "Edit_", "Prev_Ticket_", "Next_Ticket_"]
        if event == r_menu[0]:
            if self.values["-rt_grp_00-"] != "r2":
                print("daily tab is not activated")
                return
            if self._get_activated_member() != self.params.user_name:
                print("you can update only your schedule. Other user's daily table is shown now")
                # TODO : printはpopupに変更
                return
            if self._update_sch_dfs(ticket_id):
                self.r2_daily_schedule_update()

        if event == r_menu[1]:
            self.display_values_in_df_to_r1(mouse_on_prj)
            self.display_values_in_df_to_r6(mouse_on_prj)
            self.values["-r1_cbx_00-"] = True
            self.window["-r1_cbx_00-"].update(self.values["-r1_cbx_00-"])

        if event in r_menu[2:4]:
            key = event[0].lower()
            ticket_list = self.r1_ticket_connections[key]
            ticket_list.append(ticket_id)
            self.r1_ticket_connections[key] = list(set(ticket_list))
            self.display_connections_dic_to_r1_table()

        if event == "Follow_up_":
            # df = self.prj_dfs[]
            self.add_follow_up_list(mouse_on_prj)

        self.update_tabs()


    def l1_chart_draw(self):
        """
        tickets belongs to activated user are arranged in each project graph area
        tickets xy coordinates are calculated with self._calc_ticket_position.
        """
        width_ratio = self.update_l1_size_text(0)
        name = self._get_activated_member()
        self._priority_update(name=name)
        tmp_df = self._create_temporary_df_for_cal_position(self.prj_dfs[name], "ToDo")
        todo_ticket_pos_df = self._calc_ticket_position(tmp_df)
        tmp_df = self._create_temporary_df_for_cal_position(self.prj_dfs[name], "Often")
        often_ticket_pos_df = self._calc_ticket_position(tmp_df)
        time_to_pix = 100 / self.params.hour_in_date
        task_font_size = int(self.window["-l1_txt_02-"].get())
        # draw calendar top of the L1 tab
        begin_day = datetime.date.today()
        if width_ratio <= -50:
            l1_calendar = [begin_day + relativedelta(months=i) for i in range(100)]
            txt = [d.strftime("%m") for d in l1_calendar]
            # 100(base) / 20(days in month) = 5
            ticket_width_ratio = 5 * ((100 + width_ratio)//25)
            width_ratio = 100 * (100 + width_ratio)//25
        elif width_ratio <= 0:
            l1_calendar = [begin_day + datetime.timedelta(weeks=i) for i in range(100)]
            txt = [d.strftime("%m/%d") for d in l1_calendar]
            # 100(base) / 5(days/week) = 20
            ticket_width_ratio = 20 * ((50 + width_ratio)//25)
            width_ratio = 100 * (50 + width_ratio)//25
        elif width_ratio <= 50:
            l1_calendar = [begin_day + datetime.timedelta(days=i) for i in range(100)]
            txt = [d.strftime("%d") for d in l1_calendar if d.weekday() < 5]
            ticket_width_ratio = width_ratio
        else:
            l1_calendar = [begin_day + datetime.timedelta(days=i) for i in range(100)]
            txt = [d.strftime("%m/%d(%a)") for d in l1_calendar if d.weekday() < 5]
            ticket_width_ratio = width_ratio

        self.l1_grp_cal.erase()
        font_size = min(self.params.font_size * width_ratio // 100, self.params.font_size)
        font_size = self.params.font_size
        for i, t in enumerate(txt):
            self.l1_grp_cal.draw_text(t, (width_ratio//2+i*width_ratio, 50), color=self.theme.text, font=(self.params.font, font_size))
            self.l1_grp_cal.draw_line((i*width_ratio, 0), (i*width_ratio, 100), color=self.theme.text, width=1)
        left_edge = self.sizes.graph_top_right_w
        self.l1_grp_cal2.draw_text("tickets", (left_edge // 2, 50), color=self.theme.text, font=(self.params.font, self.params.font_size))
        self.l1_grp_cal2.draw_line((left_edge, 0), (left_edge, 100), color=self.theme.text, width=1)

        # ticket id and position list. these are used to know which ticket mouse cursor is on
        self.graph_positions_todo = [[0] for i in range(len(self.prj))]
        self.graph_ticket_ids_todo = [[] for i in range(len(self.prj))]
        # self.graph_positions_often = [[0] for i in range(len(self.prj))]
        self.graph_ticket_ids_often = [[] for i in range(len(self.prj))]

        # draw tickets on each task graph
        for prj_id, prj in enumerate(self.prj):
            self.l1_grp[prj_id].erase()
            self.l1_grp2[prj_id].erase()
            self.l1_grp2[prj_id].draw_line((left_edge, 0), (left_edge, 100), color=self.theme.graph_line, width=3)
            todo_tmp = todo_ticket_pos_df[todo_ticket_pos_df["prj"] == prj].copy()
            often_tmp = often_ticket_pos_df[often_ticket_pos_df["prj"] == prj].copy()
            todo_tmp["begin_pos"] = (todo_tmp["begin_pos"] * ticket_width_ratio) // 100
            todo_tmp["end_pos"] = (todo_tmp["end_pos"] * ticket_width_ratio) // 100
            # todo
            for turn in ["draw_rectangle", "draw_text"]:
                prev_task = ""
                i = -1
                for idx in todo_tmp.index:
                    i += 1
                    items = todo_tmp.loc[idx]
                    x0, x1 = int(items["begin_pos"]), int(items["end_pos"])
                    y0 = -(i % 3) * 30 + 80
                    used_hour = items["Man_hour_reg"] * time_to_pix * ticket_width_ratio // 100
                    xp = max(0, x0 - used_hour)

                    is_continues = False
                    if items["Task"] == prev_task:
                        is_continues = True
                    prev_task = items["Task"]
                    
                    if self.values["-l1_cbx_04-"] and is_continues: # combine
                        i -= 1
                        y0 =  -(i % 3) * 30 + 80

                    if turn == "draw_rectangle":
                        color = items["Color"] if items["Color"] else self.theme.graph_unknown
                        self.l1_grp[prj_id].draw_rectangle((xp, y0-15), (x0, y0+15), line_color=color, line_width=1)
                        self.l1_grp[prj_id].draw_rectangle((x0, y0-15),(x1, y0+15), fill_color=color, line_color=color, line_width=1)

                        # color set depend on due date
                        if todo_tmp.loc[idx, "over"] == None:
                            color = self.theme.graph_vertical_line
                            width = 1
                        elif todo_tmp.loc[idx, "over"] == False:
                            color = self.theme.graph_vertical_line_due
                            width = 2
                        else:
                            color = self.theme.alert
                            width = 3
                        self.l1_grp[prj_id].draw_line((x1, 0), (x1, 100), color=color, width=width)

                        if self.graph_positions_todo[prj_id][-1] >= x0:
                            self.graph_positions_todo[prj_id].append(x1)
                            self.graph_ticket_ids_todo[prj_id].append(idx)
                        else:
                            self.graph_positions_todo[prj_id].extend([x0, x1])
                            self.graph_ticket_ids_todo[prj_id].extend([None, idx])
                    
                    else:
                        if is_continues:
                            tt1, tt2 = "", ""
                        else:
                            tt1, tt2 = f" {items['Task']}", ""
                        if not self.values["-l1_cbx_04-"]: # combine
                            if self.values["-l1_cbx_01-"]: # in charge
                                tt2 += f" {items['In_charge']}"
                            if self.values["-l1_cbx_02-"]: # hour
                                tt2 += f" ({items['Man_hour_reg']:2.2f}/{items['Update_Estimation']:2.2f})"
                            if self.values["-l1_cbx_03-"]: # ticket
                                if tt2:
                                    tt1 += f"-{items['Ticket']}"
                                else:
                                    tt2 = f" {items['Ticket']}"

                        self.l1_grp[prj_id].draw_text(tt1, (x0, y0+7), color=self.theme.graph_text, font=(self.params.font, task_font_size), text_location=sg.TEXT_LOCATION_LEFT)
                        self.l1_grp[prj_id].draw_text(tt2, (x0, y0-7), color=self.theme.graph_text, font=(self.params.font, task_font_size-1), text_location=sg.TEXT_LOCATION_LEFT)

            self.graph_positions_todo[prj_id].append(999999)
            self.graph_ticket_ids_todo[prj_id].append(None)

            # often
            if len(often_tmp.index) < 1:
                continue
            num_col = (len(often_tmp.index) - 1)// 5 + 1
            ticket_width = left_edge // num_col
            self.graph_ticket_ids_often[prj_id] = [[None for _ in range(num_col)] for _ in range(5)]
            for i, idx in enumerate(often_tmp.index):
                items = often_tmp.loc[idx]
                col = i // 5
                row = i % 5
                x0 = col * ticket_width
                x1 = x0 + ticket_width
                y0 = -row * 18 + 86
                color = items["Color"] if items["Color"] else self.theme.graph_unknown
                self.l1_grp2[prj_id].draw_rectangle((x0+100, y0-7),(x1-100, y0+7), fill_color=color, line_color=color, line_width=1)
                self.l1_grp2[prj_id].draw_text(f" {items['Task']}-{items['Ticket']}", (x0, y0), color=self.theme.graph_text, font=(self.params.font, task_font_size), text_location=sg.TEXT_LOCATION_LEFT)
                self.l1_grp2[prj_id].draw_line((x0, 0), (x0, 100), color=self.theme.graph_vertical_line, width=1)
                self.graph_ticket_ids_often[prj_id][row][col] = idx

        if not self.values:
            return

        for i, (todo_ids, often_ids) in enumerate(zip(self.graph_ticket_ids_todo, self.graph_ticket_ids_often)):
            # flag_exist = (len(todo_ids) - 1 + len(often_ids)) > 0
            flag_exist = len(todo_ids) > 1
            flag_exist = flag_exist if self.prj[i] not in self.personal_memo["set"]["prj"] else 1
            self.values[f"-hd_cbx_{i:02d}-"] = flag_exist
            self.window[f"-hd_cbx_{i:02d}-"].update(flag_exist)
        self.show_prj_boxes_as_chk_box()


    def update_l1_size_text(self, up_down):
        d2p = {"monthly 1":-75, "monthly 2":-50, "weekly 1":-25, "weekly 2":0}
        for i in range(1, 13):
            d2p[f"{i*25}%"] = i*25
        p2d = {v:k for k, v in d2p.items()}
        width_text = self.window["-l1_txt_00-"].get()
        width = d2p[width_text]
        new_width = width + up_down * 25
        if -75 <= new_width <= 300:
            width = new_width
        self.window["-l1_txt_00-"].update(p2d[width])
        return width

    def enlarge_l1_chart(self):
        width = self.update_l1_size_text(1)
        self.l1_chart_draw()
    
    def shrink_l1_chart(self):
        width = self.update_l1_size_text(-1)
        self.l1_chart_draw()

    def change_font_size(self, pm):
        font_size = int(self.window["-l1_txt_02-"].get())
        font_size += pm
        self.window["-l1_txt_02-"].update(f"{font_size}")
        self.l1_chart_draw()


    # l2 =======================================================================
    # not implemented

    # l3 =======================================================================
    def update_priority_as_per_button_pressed(self, eid):
        """
        WARNING!! currently auto priority function is used. This function is not used.
        priority of selected ticket is changed depending on the button. 
        And update table
        Args:
            eid (int): button id
        """

        ticket_id = self.get_selected_ticket_id_in_table()
        if not ticket_id:
            return
        # Update the step value prevent overflow
        current_pri = self.prj_dfs[self.params.user_name].loc[ticket_id, "Priority"].item()
        steps = [-10, -1, 2, 11]
        step = max(1, current_pri + steps[eid]) - current_pri
        self._priority_update(ticket_id=ticket_id, step=step)
        self.display_l3_table_as_multiline_command(ticket_id)

        return


    def update_l3_table(self, ticket_id=None):
        # currently not used. display_l3_table_as_multiline_command is used.
        name = self._get_activated_member()
        l3_tbl_df = self.prj_dfs[name][self.params.priority_list]
        row = self.prj_dfs[name].index.get_loc(ticket_id) if ticket_id else 0

        table_colors = [[] for _ in range(l3_tbl_df.shape[0])]
        for i, tid in enumerate(l3_tbl_df.index.values.tolist()):
            if l3_tbl_df.loc[tid, "Status"] == "Done":
                table_colors[i] = [i, self.theme.table_ticket_done]
            elif l3_tbl_df.loc[tid, "Status"] == "Often":
                table_colors[i] = [i, self.theme.table_ticket_often]
            else:
                table_colors[i] = [i, self.theme.table_ticket_other]
        self.window["-l3_tbl_00-"].update(values=l3_tbl_df.values.tolist(), select_rows=[row], row_colors=table_colors)


    def l3_table_selected_ticket_changed(self):
        """call this function When a row of left 3 table is clicked 
           Display the detail of ticket on r1 tab. 
           Remain ticket id for use next other event like right click menu. 
        """

        ticket_id = self.get_selected_ticket_id_in_table()

        if not ticket_id:
            return
        self.previous_selected_ticket = ticket_id

        if self.values["-r1_cbx_00-"]:
            return

        flag_is_ticket, mouse_on_prj = self._get_is_ticket_and_series_from_ticket_id(ticket_id)
        if flag_is_ticket:
            self.display_values_in_df_to_r1(mouse_on_prj)

        self.schedule_ticket_to_daily_table()

        return


    def get_selected_ticket_id_in_table(self):
        if not self.values["-l3_tbl_00-"]:
            return None
        indices = [self.l3_tbl_df.index.values[row] for row in self.values["-l3_tbl_00-"]]
        ticket_id = indices[0]
        return ticket_id


    def calculate_priority(self):
        df = self.prj_dfs[self.params.user_name].copy()
        df = df[df["Status"] != "Done"]
        df = df.query("Project1 != 'Other' or Project2 != 'Regularly'")

        st = SortTickets(df, self.params.hour_in_date)
        st.calc_priority()

        for i, tid in enumerate(st.sorted_tid):
            self.prj_dfs[self.params.user_name].loc[tid, "Priority"] = i + 1
            # print(df.loc[tid, "Task"], df.loc[tid, "Ticket"], i)

        self._priority_update()


    def _convert_df_str_to_datetime_l3_tbl(self, df):
        date_col = ["Ready_date", "Due_date", "End_date_reg"]
        for col in date_col:
            df[col] = pd.to_datetime(df[col], format=r"%Y/%m/%d")
        return df

    def _convert_df_datetime_to_str_l3_tbl(self, df):
        date_col = ["Ready_date", "Due_date", "End_date_reg"]
        for col in date_col:
            df[col] = df[col].dt.strftime(r"%Y/%m/%d")
            df.loc[df[col] != df[col], col] = ""
        return df


    def display_l3_table_as_multiline_command(self, ticket_id=None):

        name = self._get_activated_member()
        self.l3_tbl_df = self.prj_dfs[name][self.params.priority_list[:-1]].copy()
        self.l3_tbl_df["Index"] = self.l3_tbl_df.index
        self.l3_tbl_df = self._convert_df_str_to_datetime_l3_tbl(self.l3_tbl_df)
        query_arg = self.window["-l3_inp_00-"].get()
        sort_arg = self.window["-l3_inp_01-"].get()
        sort_arg = sort_arg.replace("'", "").replace('"', "")
        sort_arg = sort_arg.replace(" ", "").replace('"', "")
        sort_arg = sort_arg.split(",")

        self.window["-l3_txt_00-"].update('input 1st arg of df.query() like Project1 == "TEST" and Status in ("ToDo", "Done")', background_color=self.theme.input_box)
        self.window["-l3_txt_01-"].update('input sort item(s) like "Man_hour_reg", "End_date_reg"', background_color=self.theme.input_box)

        if query_arg:
            try:
                self.l3_tbl_df = self.l3_tbl_df.query(query_arg)
            except Exception as e:
                self.window["-l3_txt_00-"].update(e, background_color=self.theme.alert)
        if sort_arg[0]:
            try:
                self.l3_tbl_df = self.l3_tbl_df.sort_values(sort_arg)
            except Exception as e:
                self.window["-l3_txt_01-"].update(e, background_color=self.theme.alert)

        table_colors = [[] for _ in range(self.l3_tbl_df.shape[0])]
        for i, tid in enumerate(self.l3_tbl_df.index.values.tolist()):
            if self.l3_tbl_df.loc[tid, "Status"] == "Done":
                table_colors[i] = [i, self.theme.table_ticket_done]
            elif self.l3_tbl_df.loc[tid, "Status"] == "Often":
                table_colors[i] = [i, self.theme.table_ticket_often]
            else:
                table_colors[i] = [i, self.theme.table_ticket_other]

        row = 0
        if ticket_id and ticket_id in self.l3_tbl_df.index:
            row = self.l3_tbl_df.index.get_loc(ticket_id)
        
        self.l3_tbl_df = self._convert_df_datetime_to_str_l3_tbl(self.l3_tbl_df)
        if self.l3_tbl_df.values.tolist():
            self.window["-l3_tbl_00-"].update(values=self.l3_tbl_df.values.tolist(), select_rows=[row], row_colors=table_colors)
            self.personal_memo["set"]["table_query"] = query_arg
            self.personal_memo["set"]["table_sort"] = ",".join(sort_arg)

        return

    # l4 =======================================================================
    def display_order_list_in_l4(self):
        
        table, table_color = [], []
        flag_to_me = False
        for i, idx in enumerate(self.order_dic.keys()):
            maker, df = self.order_dic[idx]
            row = [maker] + df.loc[idx, ["In_charge", "Project1", "Project2", "Task", "Ticket", "Due_date"]].values.tolist() + [idx]
            table.append(row)

            c = self.theme.order_ticket_someone
            if row[1] == self.params.user_name:
                c = self.theme.order_ticket_mine
                flag_to_me = True
            table_color.append([i, c])

        self.window["-l4_tbl_00-"].update(values=table, row_colors=table_color)
        self.header_alert_update(flag_to_me, "Order")


    def delete_order_tickets(self, idx):

        maker, _ = self.order_dic[idx]
        file = self.ord_file.replace("--name--", maker).replace("--index--", idx)
        if os.path.exists(file):
            try:
                os.remove(file)
            except:
                sg.popup_ok("Order ticket file couldn't be removed")
        else:
            sg.popup_ok("Order ticket file couldn't be found")


    def accept_order(self):
        
        row_list = self.values["-l4_tbl_00-"]
        if not row_list:
            return

        for row in row_list:
            row = self.window["-l4_tbl_00-"].get()[row]
            in_charge = row[1]
            idx = row[7]
            _, input_df = self.order_dic[idx]
            
            if in_charge == self.params.user_name:
                if idx in self.prj_dfs[self.params.user_name].index.values.tolist():
                    if sg.popup_ok_cancel("same ticket is already exist. remove order ticket file ?") == "OK":
                        self.delete_order_tickets(idx)
                    continue

                self.prj_dfs[in_charge] = self.prj_dfs[in_charge].append(input_df)
                self.update_prev_next_task(input_df, update_items={})
                sg.popup_no_buttons("new ticket has been added", auto_close=True, auto_close_duration=1)
                self.delete_order_tickets(idx)

                # update current exist prj dictionaries
                prj = "-".join([input_df["Project1"].item(), input_df["Project2"].item()])
                self.dic_prj1_2[input_df["Project1"].item()].add(input_df["Project2"].item())
                self.dic_prj_task[prj].add(input_df["Task"].item())
                self.prj = sorted(list(self.dic_prj_task.keys()))

        self.save_files()
        self.read_order()
        self.update_tabs()


    def deny_order(self):

        row_list = self.values["-l4_tbl_00-"]
        if not row_list:
            return

        for row in row_list:
            row = self.window["-l4_tbl_00-"].get()[row]
            in_charge = row[1]
            idx = row[7]

            if sg.popup_ok_cancel(f"delete {row[5]} ({row[1]}). OK ??") == "OK":
                self.delete_order_tickets(idx)

        self.read_order()
        self.update_tabs()


    # l5 =======================================================================
    def display_follow_up_tickets(self):

        follow_items = self.personal_memo["follow"]

        prj_dfs = [df for df in self.prj_dfs.values()]
        prj_df = pd.concat(prj_dfs, axis=0)
        ord_dfs = [df for _, df in self.order_dic.values()]
        ord_df = pd.concat(ord_dfs, axis=0)

        prj_idx, ord_idx, deleted_items = [], [], []
        for item in follow_items:
            if item[0] in prj_df.index:
                prj_idx.append(item[0])
            elif item[0] in ord_df.index:
                ord_idx.append(item[0])
            else:
                deleted_items.append(item)

        prj_df = prj_df.loc[prj_idx]
        ord_df = ord_df.loc[ord_idx]
        ord_df["Status"] = "To Be Approved"
        df = pd.concat([prj_df, ord_df], axis=0)
        display_columns = ["Project1", "Project2", "Task", "Ticket", "Due_date", "In_charge", "Status"]
        df = df[display_columns]

        # add info because deleted ticket info exist only follow memo
        for idx, prj1, prj2, task, ticket, in_charge in deleted_items:
            df.loc[idx] = ""
            df.loc[idx, "Project1"] = prj1
            df.loc[idx, "Project2"] = prj2
            df.loc[idx, "Task"] = task
            df.loc[idx, "Ticket"] = ticket
            df.loc[idx, "In_charge"] = in_charge
            df.loc[idx, "Status"] = "Deleted"

        df["title"] = df["Project1"] + "-" + df["Project2"] + "-" + df["Task"] + "-" + df["Ticket"]
        df.sort_values("title", inplace=True)

        table = df.reset_index().values.tolist()
        color_table = []
        for i, row in enumerate(table):
            if row[7] == "Deleted":
                c = self.theme.follow_ticket_deleted
            elif row[7] == "To Be Approved":
                c = self.theme.follow_ticket_to_be_approved
            elif row[7] == "ToDo":
                c = self.theme.follow_ticket_todo
            elif row[7] == "Done":
                c = self.theme.follow_ticket_done
            else:
                c = self.theme.follow_ticket_other
            color_table.append([i, c])
        self.window["-l5_tbl_00-"].update(values=table, row_colors=color_table)


        msg = f"""
        following {len(table)} items
        """

        df2 = df[["title", "Status"]]
        df2 = df2.groupby("title")

        flag_complete = False
        for title, df in df2:
            status = list(set(df["Status"].values.tolist()))
            if not status:
                continue
            if len(status) > 1:
                continue
            if status[0] == "Done":
                msg += f"【{title} completed !】"
                flag_complete = True

        self.window["-l5_txt_00-"].update(msg)
        self.header_alert_update(flag_complete, "Follow")


    def add_follow_up_list(self, df):
        if type(df) == pd.core.series.Series:
            idx = df.name
            prj1 = df["Project1"]
            prj2 = df["Project2"]
            task = df["Task"]
            ticket = df["Ticket"]
            in_charge = df["In_charge"]
        else:
            idx = df.index[0]
            prj1 = df.loc[idx, "Project1"]
            prj2 = df.loc[idx, "Project2"]
            task = df.loc[idx, "Task"]
            ticket = df.loc[idx, "Ticket"]
            in_charge = df.loc[idx, "In_charge"]
        self.personal_memo["follow"].append([idx, prj1, prj2, task, ticket, in_charge])


    def delete_follow_ticket(self):
        row_list = self.values["-l5_tbl_00-"]
        if not row_list:
            return

        for row in row_list:
            row = self.window["-l5_tbl_00-"].get()[row]
            idx = row[0]
            print(idx)
        
            for i, item in enumerate(self.personal_memo["follow"]):
                if idx == item[0]:
                    break
            del self.personal_memo["follow"][i]
        
        self.update_tabs()




# ==========================================================================
# functions for right tabs
#===========================================================================
    # rt =======================================================================
    def set_right_click_menu_of_daily_table(self):
        df = self.prj_dfs[self.params.user_name].query("Status == 'Often'").copy()

        df["prj12"] = df["Project1"] + "-" + df["Project2"]
        df["tt"] = df["Task"] + "-" + df["Ticket"]
        df["title"] = df["prj12"] + "-" + df["tt"]
        df.sort_values("title", inplace=True)
        menu = {}
        self.rid2idx = {}
        rmenu = None
        for i, idx in enumerate(df.index):
            prj12 = df.loc[idx, "prj12"] 
            if prj12 not in menu.keys():
                menu[prj12] = []
            k = f"{hex(i)[2:]:X>4}"
            menu[prj12].append(df.loc[idx, "tt"] + f" : <{k}>")
            self.rid2idx[k] = idx

            rmenu = []
            for i, (k, v) in enumerate(menu.items()):
                rmenu.extend([k, v])
            rmenu = ["r-menu of right click"] + [rmenu]
            # rmenu = ["A", ["B", ["B1", "B2"], "C", ["C1", "C2"]]]

        if rmenu:
            self.window[f"-r2_tbl_00-"].set_right_click_menu(rmenu)
        
        return

    # r1 =======================================================================
    def select_date_for_date_box(self, eid):
        """selecting date by using calendar 
        Args:
            eid (int): input box id defined _r1_layout
        """
        ymd = datetime.date.today()
        ret = popup_get_date(start_year=ymd.year, start_mon=ymd.month, start_day=ymd.day, begin_at_sunday_plus=1, close_when_chosen=True, keep_on_top=True, no_titlebar=False)
        if ret:
            (m, d, y) = ret
            self.values[f"-r1_inp_{eid:02d}-"] = f"{y}/{m}/{d}"
            self.window[f"-r1_inp_{eid:02d}-"].update(self.values[f"-r1_inp_{eid:02d}-"])
        self.set_color_of_boxes_inputted_invalid_value_r1()
        return 


    def _update_input_box_color(self, tab, eid, c):
        colors = [self.theme.input_box, self.theme.warning, self.theme.alert]  #[white, yellow, red]
        self.window[f"-r{tab}_inp_{eid:02d}-"].update(background_color=colors[c])
        return c


    def _can_convert_datetime(self, str):
        try:
            datetime.datetime.strptime(str, r"%Y/%m/%d")
            return True
        except:
            return False


    def _can_convert_float025(self, str):
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


    def set_color_of_boxes_inputted_invalid_value_r1(self):
        """
        checking if values in r1 input box are valid.
        values is valid -> box color set white
        project1,2 and task are inputted but new -> box color set yellow
        values is invalid -> box color set red

        Returns:
            list : each box error value.
                   0 is "valid", 1 is "valid with caution", 2 is "invalid"
        """

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
        errors[4] = 0 if self._can_convert_datetime(self.values[f"-r1_inp_04-"]) else 2
        errors[4] = 0 if self.values[f"-r1_inp_04-"] == "" else errors[4]
        errors[5] = 0 if self._can_convert_datetime(self.values[f"-r1_inp_05-"]) else 2
        errors[5] = 0 if self.values[f"-r1_inp_05-"] == "" else errors[5]
        errors[6] = 0 if self._can_convert_float025(self.values[f"-r1_inp_06-"]) else 2
        errors[7] = 0 if self._can_convert_float025(self.values[f"-r1_inp_07-"]) else 2
        errors[8] = 0
        errors[9] = 0
        errors[10] = 0

        for eid in range(len(self.r1_inp)):
            self._update_input_box_color(1, eid, errors[eid])

        return errors


    def set_color_of_boxes_inputted_invalid_value_r6(self):
        """
        checking if values in r6 input box are valid.
        values is valid -> box color set white
        project1,2 and task are inputted but new -> box color set yellow
        values is invalid -> box color set red

        Returns:
            list : each box error value.
                   0 is "valid", 1 is "valid with caution", 2 is "invalid"
        """

        for i in range(3):
            self.values[f"-r6_inp_{i:02d}-"] = self.values[f"-r6_inp_{i:02d}-"].replace(" ", "").replace("　", "")
            self.window[f"-r6_inp_{i:02d}-"].update(self.values[f"-r6_inp_{i:02d}-"])

        # if input values is new, cell color is changed to yellow
        prj1 = self.values[f"-r6_inp_00-"]
        prj2 = self.values[f"-r6_inp_01-"]
        exist_prj_1 = prj1 in self.dic_prj1_2.keys()
        prj2_candidates = self.dic_prj1_2[prj1] if exist_prj_1 else []
        exist_prj_2 = prj2 in prj2_candidates
        exist_prj_12 = f"{prj1}-{prj2}" in self.dic_prj_task.keys()
        task_candidates = self.dic_prj_task[f"{prj1}-{prj2}"] if exist_prj_12 else []

        errors = [2] * len(self.r6_inp)
        errors[0] = 0 if exist_prj_1 else 1
        errors[0] = 2 if prj1 == "" else errors[0]
        errors[1] = 0 if exist_prj_2 else 1
        errors[1] = 2 if prj2 == "" else errors[1]
        errors[2] = 0 if self.values[f"-r6_inp_02-"] in task_candidates else 1
        errors[2] = 2 if self.values[f"-r6_inp_02-"] == "" else errors[2]

        for eid in range(len(self.r6_inp)):
            self._update_input_box_color(6, eid, errors[eid])

        return errors


    def _error_popup(self, errors):            
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
    

    def is_valid_prev_next_tickets(self, ticket_id):
        p_tickets = self.r1_ticket_connections["p"]
        n_tickets = self.r1_ticket_connections["n"]
        
        both_included = list(set(p_tickets) & set(n_tickets))
        if both_included:
            tid = both_included[0]
            c, ds = self._get_is_ticket_and_series_from_ticket_id(tid)
            if not c:
                sg.popup_ok("something is wrong")
                return False
            msg = f"{ds['Project1']}-{ds['Project2']}-{ds['Task']}-{ds['Ticket']}"
            sg.popup_ok(msg + "\nis in both prev_tickets and next_tickets")
            return False

        m = ""
        if ticket_id in p_tickets:
            m += " prev_tickets"
        if ticket_id in n_tickets:
            m += " next_tickets"
        if m:
            sg.popup_ok(f"ticket itself is in {m}")
            return False
        
        return True
    

    def create_ticket_as_r1(self):
        """ticket contents update or create new
        """

        errors = self.set_color_of_boxes_inputted_invalid_value_r1()
        ep = self._error_popup(errors)
        if ep > 0:
            return

        if not self.is_valid_prev_next_tickets(""):
            return
        # create new ticket dataframe from r1 input panel
        input_df = self.update_df_as_per_r1_inputs()
        ticket_id = input_df.index[0]
        in_charge = input_df["In_charge"].item()
            
        if in_charge == self.params.user_name:
            self.prj_dfs[in_charge] = self.prj_dfs[in_charge].append(input_df)
            update_items = {}
            update_items["Prev_task"] = ["", input_df["Prev_task"].item()]
            update_items["Next_task"] = ["", input_df["Next_task"].item()]
            self.update_prev_next_task(ticket_id, update_items)

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

        oc = sg.popup_ok_cancel(f"ticket will be sent to {in_charge}. is it OK ?") 
        if oc == "OK":
            input_df["Prev_task"] = ""
            input_df["Next_task"] = ""
            if in_charge == "Assign to all":
                for name in self.params.team_members:
                    input_df["In_charge"] = name
                    old_index = input_df.index[0]
                    new_index = self._str_to_hash_id(input_df.values.tolist()[0], self.params.columns)
                    input_df.rename(index={old_index : new_index}, inplace=True)
                    self._save_order(input_df)
                    self.add_follow_up_list(input_df)
            else:
                self._save_order(input_df)
                self.add_follow_up_list(input_df)
            self.read_order()
            self.update_tabs()
            return


    def update_ticket_as_r1(self):
        """update ticket values
        """

        # get current ticket info due to popup confirmation
        ticket_id = self.window["-r1_txt_04-"].get()
        _, current_ds = self._get_is_ticket_and_series_from_ticket_id(ticket_id)

        # get input info to update
        errors = self.set_color_of_boxes_inputted_invalid_value_r1()
        ep = self._error_popup(errors)
        if ep > 0:
            return
        input_df = self.update_df_as_per_r1_inputs()
        input_df.rename(index={input_df.index[0] : ticket_id}, inplace=True)

        # exception handling
        if current_ds["In_charge"] != self.params.user_name:
            sg.popup_ok("you can update only your ticket")
            return
        if input_df.loc[ticket_id, "In_charge"] != self.params.user_name:
            sg.popup_ok("please create new ticket when update ticket in charge")
            return
        if not self.is_valid_prev_next_tickets(ticket_id):
            return

        # popup. user update input boxes, user can not know current values. so confirm the update contents 
        update_items = {} # column : [previous, new]
        msg = ""
        for column in self.params.columns:
            if column in self.params.not_updatable_columns:
                continue
            if input_df.loc[ticket_id, column] != current_ds[column]:
                update_items[column] = [current_ds[column], input_df.loc[ticket_id, column]]
                # if column in ["Prev_task", "Next_task"]:
                msg += f"{column} : {current_ds[column]} -----> {input_df.loc[ticket_id, column]}\n"

        if not msg or sg.popup_ok_cancel(msg) != "OK":
            return

        # update df 
        flag_order_changed = False
        for column, (_, new) in update_items.items():
            self.prj_dfs[self.params.user_name].loc[ticket_id, column] = new
            if column in ["Prev_task", "Next_task"]:
                flag_order_changed = True

        if flag_order_changed:
            self.update_prev_next_task(ticket_id, update_items)
        self.update_tabs()
        self._r1_pre_next_ticket_table_update()
        
        sg.popup_no_buttons("update ticket items", auto_close=True, auto_close_duration=1)


    def delete_ticket_as_r1(self):
        """delete the ticket
        1. get the ticket id
        2. if mon hour recode of the ticket is NOT 0, stop deleting.
        3. delete ticket
        4. delete ticket id in TO, FROM of opponent tickets.  
        """

        # 1. ticket id
        ticket_id = self.window["-r1_txt_04-"].get()
        _, delete_ds = self._get_is_ticket_and_series_from_ticket_id(ticket_id)

        user_name = self.params.user_name
        if not ticket_id in self.prj_dfs[user_name].index:
            sg.popup_ok("Invalid ticket")
            return

        if delete_ds["In_charge"] != user_name:
            sg.popup_ok("you can delete only your ticket")
            return 

        # 2. check exist recode
        if self.prj_dfs[user_name].loc[ticket_id, "Man_hour_reg"].item() != 0:
            sg.popup_ok("CAN NOT delete. this ticket has been already tracked in recode.")
            return

        # 2-2 check exist in daily schedule
        col = self.window["-r2_txt_02-"].get()
        sch_user = self.sch_dfs[user_name][col].tolist()
        sch_user = sch_user[:24*4]
        if delete_ds.name in sch_user:
            sg.popup_ok("CAN NOT delete. this ticket is scheduled in daily table.")
            return

        msg = "delete ticket ok ???\n\n"
        for column in self.params.columns:
            if column in self.params.not_updatable_columns:
                continue
            msg += f"{column} : {self.prj_dfs[user_name].loc[ticket_id, column]}\n"

        if sg.popup_ok_cancel(msg) != "OK":
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


    def update_prev_next_task(self, ticket_id, update_items):
        """update the tickets which are selected as previous or next ticket of new ticket 
           add new ticket id to "next ticket" of "previous ticket".
           add new ticket id to "previous ticket" of "next ticket".
        Args:
            input_df (pandas dataframe): update or new ticket dataframe
            update_items (dictionary) : include current prev and next task ids.
        """

        name = self.params.user_name
        keys = ["Prev_task", "Next_task"]
        for key, opp_key in zip(keys, keys[::-1]):
            old_conn_ids, new_conn_ids = update_items.get(key, ["", ""])
            old_conn_ids = set(old_conn_ids.split(","))
            new_conn_ids = set(new_conn_ids.split(","))

            deleted_ids = old_conn_ids - new_conn_ids
            added_ids = new_conn_ids - old_conn_ids

            for tid in deleted_ids:
                if not tid:
                    continue
                tmp = self.prj_dfs[name].loc[tid, opp_key]
                tmp = tmp.split(",")
                if ticket_id in tmp:
                    tmp.remove(ticket_id)
                    self.prj_dfs[name].loc[tid, opp_key] = ",".join(tmp)

            for tid in added_ids:
                if not tid:
                    continue
                tmp = self.prj_dfs[name].loc[tid, opp_key]
                tmp = tmp.split(",")
                if ticket_id not in tmp:
                    tmp.append(ticket_id)
                    self.prj_dfs[name].loc[tid, opp_key] = ",".join(tmp)


    def display_values_in_df_to_r1(self, df):
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
        
        k = f"-r1_txt_04-"
        self.values[k] = df.name
        self.window[k].update(df.name)

        k = "-r1_cmb_00-"
        self.values[k] = df["In_charge"]
        self.window[k].update(self.values[k])
        k = "-r1_cmb_01-"
        self.values[k] = df["Status"]
        self.window[k].update(self.values[k])

        self._r1_pre_next_ticket_table_update(df)
        self.set_color_of_boxes_inputted_invalid_value_r1()
        self.set_right_click_menu_of_prj12_task()


    def display_values_in_df_to_r6(self, df):

        input_values = [df["Project1"], df["Project2"], df["Task"]]
        for i in range(3):
            k = f"-r6_inp_{i:02d}-"
            self.values[k] = input_values[i]
            self.window[k].update(self.values[k])


    def update_df_as_per_r1_inputs(self):
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

        r1_inputs = [self.values[f"-r1_inp_{i:02d}-"] for i in range(len(self.r1_inp))]

        prev_ticket = self.r1_ticket_connections["p"]
        next_ticket = self.r1_ticket_connections["n"]
        prev_ticket = ",".join(prev_ticket)
        next_ticket = ",".join(next_ticket)

        def float025(s):
            return int(float(s) * 100) / 100

        ticket_new[0:4] = r1_inputs[0:4]
        ticket_new[4] = r1_inputs[9]
        ticket_new[5] = False
        ticket_new[6:8] = r1_inputs[4:6]
        ticket_new[8] = float025(r1_inputs[6])
        ticket_new[9] = sum(list(map(float025, r1_inputs[6:8])))
        ticket_new[10] = self.values["-r1_cmb_00-"]
        ticket_new[11] = prev_ticket
        ticket_new[12] = next_ticket
        ticket_new[13] = self.values["-r1_cmb_01-"]
        ticket_new[14:16] = [""]*2
        ticket_new[16] = 0
        ticket_new[17] = r1_inputs[8]
        ticket_new[18] = r1_inputs[10]
        ticket_new[19] = 0
        ticket_new[20] = self._define_ticket_color(*ticket_new[0:3])
        index = self._str_to_hash_id(ticket_new, self.params.columns)
        
        return pd.DataFrame([ticket_new], columns=self.params.columns, index=[index])


    def _r1_pre_next_ticket_table_update(self, df=None):
        """
        1. read r1 input box items 
        2. make list which has task-tickets in current prj and show r1 table
        3. select table rows which are defined in current ticket 
           if current ticket prev or next ticket is defined. 
        """
        # prj1 = self.values[f"-r1_inp_00-"]
        # prj2 = self.values[f"-r1_inp_01-"]
        # task = self.values[f"-r1_inp_02-"]
        # ticket = self.values[f"-r1_inp_03-"]
        # name = self.values[f"-r1_cmb_00-"]

        # df_tmp = self.prj_dfs[name].sort_values("Priority")
        # df_tmp = df_tmp.query(f"Project1 == '{prj1}' & Project2 == '{prj2}' & Status != 'Done'").copy()
        # df_tmp["task-ticket"] = df_tmp['Task'] + "-" + df_tmp['Ticket']
        # tickets = df_tmp["task-ticket"].values.tolist()
        # tids = df_tmp.index.tolist()
        # self.r1_tables = (["None"] + tickets, ["None"] + tids)

        # df_tmp = df_tmp.query(f"Task == '{task}' & Ticket == '{ticket}'")
        # if not df_tmp.empty:
        #     current_ticket_id = df_tmp.index.item()
        #     prev_ticket = self.prj_dfs[name].loc[current_ticket_id, "Prev_task"].split(",")
        #     next_ticket = self.prj_dfs[name].loc[current_ticket_id, "Next_task"].split(",")
        #     def_perv = [i for i, tid in enumerate(self.r1_tables[1]) if tid in prev_ticket]
        #     def_next = [i for i, tid in enumerate(self.r1_tables[1]) if tid in next_ticket]
        # else:
        #     def_perv = []
        #     def_next = []

        # self.window["-r1_tbl_02-"].update(values=self.r1_tables[0], select_rows=def_perv)
        # self.window["-r1_tbl_03-"].update(values=self.r1_tables[0], select_rows=def_next)

        # TODO : 上の要らないのは消す
        if isinstance(df, pd.core.series.Series):
            p = df["Prev_task"].split(",")
            self.r1_ticket_connections["p"] = [tid for tid in p if tid]
            n = df["Next_task"].split(",")
            self.r1_ticket_connections["n"] = [tid for tid in n if tid]
            self.display_connections_dic_to_r1_table()


    def display_connections_dic_to_r1_table(self):
        p, n = [], []
        for tid in self.r1_ticket_connections["p"]:
            c, ds = self._get_is_ticket_and_series_from_ticket_id(tid)
            if not c:
                continue
            ticket = f"{ds['Project1']}-{ds['Project2']}-{ds['Task']}-{ds['Ticket']}"
            p.append(ticket)
        for tid in self.r1_ticket_connections["n"]:
            c, ds = self._get_is_ticket_and_series_from_ticket_id(tid)
            if not c:
                continue
            ticket = f"{ds['Project1']}-{ds['Project2']}-{ds['Task']}-{ds['Ticket']}"
            n.append(ticket)
        self.window["-r1_tbl_04-"].update(values=p)
        self.window["-r1_tbl_05-"].update(values=n)
    

    def set_right_click_menu_of_prj12_task(self):

        tabs = [1, 6]
        menu1 = ["prj1", [f"Prj1:{k}." for k in self.dic_prj1_2.keys()]]
        for tab_num in tabs:
            self.window[f"-r{tab_num}_inp_00-"].set_right_click_menu(menu1)
            prj1 = self.values[f"-r{tab_num}_inp_00-"]
        if prj1 not in self.dic_prj1_2.keys():
            return
        
        menu2 = ["prj2", [f"Prj2:{k}." for k in self.dic_prj1_2[prj1]]]
        for tab_num in tabs:
            self.window[f"-r{tab_num}_inp_01-"].set_right_click_menu(menu2)
            prj2 = self.values[f"-r{tab_num}_inp_01-"]
        if prj2 not in self.dic_prj1_2[prj1]:
            return

        menu3 = ["task", [f"Task:{k}." for k in self.dic_prj_task[f"{prj1}-{prj2}"]]]
        for tab_num in tabs:
            self.window[f"-r{tab_num}_inp_02-"].set_right_click_menu(menu3)


    def input_prj12_and_task_by_right_click(self, event):

        text = event[5:-1]
        for tab_num in [1, 6]:
            if event[:4] == "Prj1":
                self.values[f"-r{tab_num}_inp_00-"] = text
                self.window[f"-r{tab_num}_inp_00-"].update(text)
            if event[:4] == "Prj2":
                self.values[f"-r{tab_num}_inp_01-"] = text
                self.window[f"-r{tab_num}_inp_01-"].update(text)
            if event[:4] == "Task":
                self.values[f"-r{tab_num}_inp_02-"] = text
                self.window[f"-r{tab_num}_inp_02-"].update(text)

        self.set_color_of_boxes_inputted_invalid_value_r1()
        self.set_color_of_boxes_inputted_invalid_value_r6()


    def delete_ticket_from_prev_next_table(self, eid):
        if eid == "Prev":
            key, table_id = "p", "04"
        if eid == "Next":
            key, table_id = "n", "05"
        rows = self.values[f"-r1_tbl_{table_id}-"]
        tickets = self.r1_ticket_connections[key]
        if not rows:
            return
        for row in rows[::-1]:
            if row > len(tickets)-1:
                continue
            del tickets[row]
        self.r1_ticket_connections[key] = tickets
        self.display_connections_dic_to_r1_table()


    # r2 =======================================================================
    def r2_daily_schedule_update(self):
        """update r2 daily schedule table. 
        r2 information box and r3 team box are also updated
        """
        r2_tbl, table_colors, r2_working_hour = self.create_daily_schedule_list()
        self.values["-r2_txt_03-"] = r2_working_hour
        self.window["-r2_txt_03-"].update(r2_working_hour)
        self.window["-r2_tbl_00-"].update(values=r2_tbl, row_colors=table_colors)
        self.display_information_in_r2()
        self.display_team_box()
        return


    def create_daily_schedule_list(self):
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
        colors_4 = [self.theme.schedule_table1, self.theme.schedule_table2, self.theme.schedule_table3, self.theme.schedule_table4]
        table_colors = [(i, colors_4[i%4]) for i in range(self.params.daily_table_rows)]

        # get each table data
        sch_col = self.window["-r2_txt_02-"].get()
        sch_user = [""] * (24*4)
        name = self._get_activated_member()
        if sch_col not in self.sch_dfs[name].columns.values.tolist():
            self.sch_dfs[name][sch_col] = ""
        sch_user = self.sch_dfs[name][sch_col].tolist()[:24*4]
        sch_time = [f"{self.params.daily_begin+i//4:02d}:{i%4*15:02d} ~" for i in range(self.params.daily_table_rows)]
        sch_user = sch_user[self.params.daily_begin*4:self.params.daily_begin*4+self.params.daily_table_rows]
        sch_app = self.app_schedule

        # combine same task
        num_rows = len(sch_user)-1
        work_rows = []
        MAKER_CONTINUE = "↓"
        for i in range(num_rows):
            if sch_user[num_rows-i] == "":
                continue
            if sch_user[num_rows-i] == sch_user[num_rows-i-1]:
                    sch_user[num_rows-i] = MAKER_CONTINUE
            work_rows.append(num_rows-i)
        if sch_user[0] != "":
            work_rows.append(0)
        
        # define table color and ticket id is changed into name
        i = -1
        while i < num_rows-1:
            i += 1
            if sch_user[i] == "":
                continue
            if sch_user[i] == MAKER_CONTINUE:
                table_colors[i] = (i, table_colors[i-1][1])
                continue

            flag_is_ticket, ticket_df = self._get_is_ticket_and_series_from_ticket_id(sch_user[i])
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
        r2_tbl = [[a, t, u] for a, t, u in zip(sch_user, sch_time, sch_app)]
        
        # HACK : 時間の計算は別の関数にする
        # calculate working_hour
        if work_rows:
            t_begin = min(work_rows)*0.25 + self.params.daily_begin
            t_end = (max(work_rows)+1)*0.25 + self.params.daily_begin
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


    def delete_items_from_daily_table(self):
        if self._get_activated_member() != self.params.user_name:
            sg.popup_ok("you can update only your schedule. Other user's daily table is shown now")
            return
        if self._update_sch_dfs(ticket_id=""):
            self.r2_daily_schedule_update()
        return


    def select_date_of_daily_table(self):
        ymd = datetime.date.today()
        ret = popup_get_date(start_year=ymd.year, start_mon=ymd.month, start_day=ymd.day, begin_at_sunday_plus=1, close_when_chosen=True, keep_on_top=True, no_titlebar=False)
        if ret:
            (m, d, y) = ret
            self.window[f"-r2_txt_02-"].update(f"{y:04d}/{m:02d}/{d:02d}")
            self.r2_daily_schedule_update()
            self.display_information_in_r2()
        return

    def daily_table_date_move_to_before_after(self, eid):
        # eid=10 -> back, eid=11 -> forward
        sign = eid - 11
        if sign:
            ymd = self.window["-r2_txt_02-"].get()
            ymd = datetime.datetime.strptime(ymd, r"%Y/%m/%d")
            td = datetime.timedelta(days=1)
            ymd += sign * td
        else:
            ymd = datetime.datetime.today()
        
        self.window[f"-r2_txt_02-"].update(datetime.datetime.strftime(ymd, r"%Y/%m/%d"))
        self.r2_daily_schedule_update()
        self.display_information_in_r2()
        return


    def record_daily_table_items(self):
        """
        Record the daily working hour for each ticket
        1. update self.trk_dfs[user]
            at first, every value of selected date column are set 0.
            And the working hour of each tickets in daily table is inputted.
        2. update self.sch_dfs[user]
            Recalculate total working hour "Man_hour_reg" from self.trk dataframe.
            The first day and the last day of days with work record 
            is set "Begin_date_reg" and "End_date_reg" respectively.
        """
        name = self.params.user_name
        col = self.window["-r2_txt_02-"].get()
        # Exception handling
        if self._get_activated_member() != name:
            return
        if datetime.date(*list(map(int, col.split("/")))) > datetime.date.today():
            return
        if col not in self.sch_dfs[name].columns.values.tolist():
            return
        
        # calculate working hour of each ticket exist in table 
        sch_user = self.sch_dfs[name][col].tolist()
        sch_user = sch_user[:24*4]
        id_hours = {}
        for ticket_id in sch_user:
            if ticket_id in id_hours:
                id_hours[ticket_id] += 0.25
            elif ticket_id != "":
                id_hours[ticket_id] = 0.25

        update_tickets = set() 
        # daily table had been already tracked, tickets in table are added in update "set"
        if col in self.trk_dfs[name].columns.values.tolist():
            update_tickets = set(self.trk_dfs[name][col].index.values.tolist())
        self.trk_dfs[name][col] = 0.0
        for ticket_id in id_hours:
            if ticket_id not in self.trk_dfs[name].index.values.tolist():
                self.trk_dfs[name].loc[ticket_id] = 0
            self.trk_dfs[name].loc[ticket_id, col] = id_hours[ticket_id]
            update_tickets.add(ticket_id)

        for ticket_id in update_tickets:
            if ticket_id not in self.prj_dfs[name].index:
                self.logger.debag("Error. try to record ticket not existed")
                continue
            ticket_record_se = self.trk_dfs[name].loc[ticket_id] 
            did_date = ticket_record_se[ticket_record_se > 0].index.values.tolist()
            did_date.sort()
            self.prj_dfs[name].loc[ticket_id, "Man_hour_reg"] = ticket_record_se.sum()
            self.prj_dfs[name].loc[ticket_id, "Begin_date_reg"] = did_date[0] if did_date else ""
            self.prj_dfs[name].loc[ticket_id, "End_date_reg"] = did_date[-1] if did_date else ""

        self.update_tabs()
        self.save_files()
        # self.get_reason_of_over_estimation_tickets(ticket_ids=update_tickets)


    def got_r2_information_data(self):
        """
        call this method when r2 information input boxes below daily table value(s) is updated.
        if activate member was user, working time and reason of overwork are showed in team tab
        """
        name = self.params.user_name
        col = self.window["-r2_txt_02-"].get()
        # Exception handling
        if self._get_activated_member() != name:
            return
        if col not in self.sch_dfs[name].columns.values.tolist():
            self.sch_dfs[name][col] = ""
        self.sch_dfs[name].loc["Hour", col] = self.window["-r2_txt_03-"].get()
        for i, idx in enumerate(self.params.schedule_add_info[1:]):
            self.sch_dfs[name].loc[idx, col] = self.values[f"-r2_inp_{i:02d}-"]        
        
        return


    def display_information_in_r2(self):
        """Read self.sch_dfs[member] and update r2 information box 
        when activate user or date is changed
        """
        # initialize
        for i, idx in enumerate(self.params.schedule_add_info[1:]):
            self.values[f"-r2_inp_{i:02d}-"] = ""
            self.window[f"-r2_inp_{i:02d}-"].update("")

        name = self._get_activated_member()
        col = self.window["-r2_txt_02-"].get()
        if col not in self.sch_dfs[name].columns.values.tolist():
            return
        for i, idx in enumerate(self.params.schedule_add_info[1:]):
            self.values[f"-r2_inp_{i:02d}-"] = self.sch_dfs[name].loc[idx, col]
            self.window[f"-r2_inp_{i:02d}-"].update(self.values[f"-r2_inp_{i:02d}-"])

        return

    def set_daily_row_as_per_right_click(self, eid):

        if self._get_activated_member() != self.params.user_name:
            print("you can update only your schedule. Other user's daily table is shown now")
            return
        if self._update_sch_dfs(self.rid2idx[eid]):
            self.r2_daily_schedule_update()
        self.update_tabs()
        return

    def select_r2_table_rows_with_mouse_click(self):
        self.r2_table_click_start = self.values["-r2_tbl_00-"]
        print(self.r2_table_click_start)

    def select_r2_table_rows_with_mouse_drag(self):
        row = self.window["-r2_tbl_00-"].user_bind_event.y // self.sizes.tbl_row_hight
        row = max(row, 1)
        row = min(row, self.params.daily_table_rows-2)
        
        if not self.r2_table_click_start:
            self.r2_table_click_start = [row]
        row_s = self.r2_table_click_start[0]
        if row_s > row:
            row_s, row = row, row_s

        select_rows = [i for i in range(row_s-1, row)]
        self.window["-r2_tbl_00-"].update(select_rows=select_rows)

        # print(self.window["-r2_tbl_00-"].Widget.yview_scroll.)
        # aa = vars(self.window["-r2_tbl_00-"].Widget.yview_scroll)
        # print(aa)
        # print(self.window["-r2_tbl_00-"].Widget.yview_scroll.__get__(0))

    def r2_table_start_release(self):
        self.r2_table_click_start = []


    # r3 =======================================================================
    def display_team_box(self):
        """update r3 team box when contents are updated
        """

        today = datetime.date.today()
        col = datetime.datetime.strftime(today, r"%Y/%m/%d")

        tmp_work = [f"name  :      Begin   ~    End    (Total)   <Break> :  reason for overwork"]
        tmp_info = []
        for i, name in enumerate(self.params.team_members):
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
    def display_plans_on_multiline(self):
        """plan tab display the monthly and weekly plan saved in pln_dfs 
           to multiline windows"""
        col = self.window["-r5_txt_00-"].get()
        name = self._get_activated_member()
        if col not in self.pln_dfs[name].columns.values.tolist():
            self.pln_dfs[name][col] = ""
        for i, txt in enumerate(self.pln_dfs[name][col]):
            self.window[f"-r5_mul_{i:02d}-"].update(txt)


    def got_plans_from_multiline(self, eid):
        """contents in multiline window is copied to dataframe
        Args:
            eid (int): multiline item id
        """
        name = self._get_activated_member()
        if name != self.params.user_name:
            return
        indices = ["month", "week1", "week2", "week3", "week4", "week5"]
        col = self.window["-r5_txt_00-"].get()
        self.pln_dfs[name].loc[indices[eid], col] = self.values[f"-r5_mul_{eid:02d}-"]

    def change_displayed_plan_on_multiline(self, eid):
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


    # r6 =======================================================================
    def _topological_sort_tickets_in_single_task(self, df):
        """topological sort

        Args:
            df (DataFrame): DataFrame of tickets in single task

        Returns:
            DataFrame : sorted DataFrame
        """
        prev_tickets = {idx : [] for idx in df.index}
        next_tickets = {idx : [] for idx in df.index}
        ready_tickets = []
        df["tmp_priority"] = 999
        for idx in df.index:
            tmp = df.loc[idx, "Prev_task"].split(",")
            for tid in tmp:
                if not tid:
                    continue
                if tid not in df.index:
                    continue
                if tid == idx:
                    continue
                prev_tickets[idx].append(tid)
                next_tickets[tid].append(idx)
            if len(prev_tickets[idx]) == 0:
                ready_tickets.append(idx)

        heapify(ready_tickets)
        pri = 0
        while ready_tickets:
            pri += 1
            tid = heappop(ready_tickets)
            df.loc[tid, "tmp_priority"] = pri
            for idx in next_tickets[tid]:
                prev_tickets[idx].remove(tid)
                if len(prev_tickets[idx]) == 0:
                    heappush(ready_tickets, idx)

        df = df.sort_values("tmp_priority")
        df = df.drop("tmp_priority", axis=1)
        return df


    def display_tickets_in_table_r6(self):
        """get ticket df as per input area in r6
        and store the df as self.task_updating_df
        """

        prj1 = self.values["-r6_inp_00-"]
        prj2 = self.values["-r6_inp_01-"]
        task = self.values["-r6_inp_02-"]

        if not prj1 or not prj2 or not task:
            return
        df = self.prj_dfs[self.params.user_name]
        df = df.query(f"Project1 == '{prj1}'and Project2 == '{prj2}' and Task == '{task}' and Status == 'ToDo'")
        df = df.sort_values("Due_date")
        self.task_updating_df = self._topological_sort_tickets_in_single_task(df)
        df = self.task_updating_df[self.params.ticket_maker_table]

        self.window["-r6_tbl_00-"].update(values=df.values.tolist())


    def table_items_into_multiline_r6(self):
        txt = ""
        for idx in self.task_updating_df.index:
            single_line = self.task_updating_df.loc[idx, ["Ticket", "Estimation", "Ready_date", "Due_date"]].values.tolist()
            single_line = [s if s else "-" for s in single_line]
            single_line = " ".join(map(str, single_line))
            txt += single_line
            txt += "\n"

        self.values["-r6_mul_00-"] = txt
        self.window["-r6_mul_00-"].update(txt)


    def multiline_item_into_table_r6(self):

        txt = self.values["-r6_mul_00-"]
        txt = txt.replace(",", " ")
        txt = [t for t in txt.splitlines() if t]
        txt = [t.split() for t in txt]
        txt = [t for t in txt if len(t) and t[0] != "#"]

        error_msg = ""
        for i, l in enumerate(txt):
            l = l + [""] * (4 - len(l))
            l = l[:4]
            l[0] = l[0]
            if self._can_convert_float025(l[1]):
                l[1] = float(l[1])  
            else:
                error_msg += f"# {l[0]} : the estimate hour is wrong value {l[1]}, changed to default 2.0 \n"
                l[1] = 2.0
            if not self._can_convert_datetime(l[2]):
                if l[2] not in ["-", ""]:
                    error_msg += f"# {l[0]} : the ready date is wrong value {l[2]}\n"
                    l[2] = ""
            if not self._can_convert_datetime(l[3]):
                if l[3] not in ["-", ""]:
                    error_msg += f"# {l[0]} : the due date is wrong value {l[3]}\n"
                    l[3] = ""
            txt[i] = l

        prj1 = self.values["-r6_inp_00-"]
        prj2 = self.values["-r6_inp_01-"]
        task = self.values["-r6_inp_02-"]
        current_tickets = self.task_updating_df["Ticket"].values.tolist()
        
        for ticket_name, estimation, ready_date, due_date in txt:
            if ticket_name in current_tickets:
                idx = self.task_updating_df.query(f"Ticket == '{ticket_name}'").index[0]
                self.task_updating_df.loc[idx, "Estimation"] = estimation
                self.task_updating_df.loc[idx, "Ready_date"] = ready_date
                self.task_updating_df.loc[idx, "Due_date"] = due_date
            else:
                items = [prj1, prj2, task, ticket_name, estimation, ready_date, due_date ]
                input_df = self._add_tickets_info_into_stored_df(items)
                self.task_updating_df = self.task_updating_df.append(input_df)

        ticket2idx = {self.task_updating_df.loc[idx, "Ticket"]:idx for idx in self.task_updating_df.index}
        self.task_updating_df["tmp_priority"] = 0
        for i, txt_list in enumerate(txt):
            idx = ticket2idx[txt_list[0]]
            self.task_updating_df.loc[idx, "tmp_priority"] = i + 1
        self.task_updating_df.sort_values("tmp_priority", inplace=True)
        self.task_updating_df.drop("tmp_priority", axis=1, inplace=True)

        df = self.task_updating_df[self.params.ticket_maker_table]
        self.window["-r6_tbl_00-"].update(values=df.values.tolist())

        txt = "\n".join([" ".join(map(str, t)) for t in txt])
        txt += "\n" + error_msg
        self.values["-r6_mul_00-"] = txt
        self.window["-r6_mul_00-"].update(txt)

        if error_msg:
            self.window["-r6_mul_00-"].update(background_color = self.theme.alert)
        else:
            self.window["-r6_mul_00-"].update(background_color = self.theme.input_box)


    def _add_tickets_info_into_stored_df(self, items):
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

        ticket_new[0] = items[0]
        ticket_new[1] = items[1]
        ticket_new[2] = items[2]
        ticket_new[3] = items[3]
        ticket_new[4] = ""
        ticket_new[5] = False
        ticket_new[6] = items[5]
        ticket_new[7] = items[6]
        ticket_new[8] = items[4]
        ticket_new[9] = items[4]
        ticket_new[10] = self.params.user_name
        ticket_new[11] = ""
        ticket_new[12] = ""
        ticket_new[13] = "ToDo"
        ticket_new[14] = ""
        ticket_new[15] = ""
        ticket_new[16] = 0
        ticket_new[17] = ""
        ticket_new[18] = ""
        ticket_new[19] = 0
        ticket_new[20] = self._define_ticket_color(*ticket_new[0:3])
        index = self._str_to_hash_id(ticket_new, self.params.columns)
        
        return pd.DataFrame([ticket_new], columns=self.params.columns, index=[index])


    def add_r6_table_data_into_dfs(self):
        # update prev- and next- tickets as per table order, because total priority is defined as per those.
        prev_idx = None
        ids = self.task_updating_df.index

        new_ids = []
        for idx in ids:
            if idx not in self.prj_dfs[self.params.user_name].index:
                new_ids.append(idx)
        # if not len(new_ids):
        #     return

        msg = f"Update {self.task_updating_df.loc[ids[0], 'Project1']} - {self.task_updating_df.loc[ids[0], 'Project2']} - {self.task_updating_df.loc[ids[0], 'Task']}\n"
        for idx in new_ids:
            msg += f"{self.task_updating_df.loc[idx, 'Ticket']} \n"
        if sg.popup_ok_cancel(msg) != "OK":
            return

        for idx in ids:
            # ticket in this task is disused but remain ticket of other task
            # previous
            prev_tickets = self.task_updating_df.loc[idx, "Prev_task"].split(",")
            prev_tickets = [p for p in prev_tickets if p not in ids]
            if prev_idx:
                prev_tickets.append(prev_idx)
            self.task_updating_df.loc[idx, "Prev_task"] = ",".join(prev_tickets)

            # next
            if prev_idx:
                next_tickets.append(idx)
                self.task_updating_df.loc[prev_idx, "Next_task"] = ",".join(next_tickets)
            next_tickets = self.task_updating_df.loc[idx, "Next_task"].split(",")
            next_tickets = [n for n in next_tickets if n not in ids]
            prev_idx = idx

        self.task_updating_df.loc[prev_idx, "Next_task"] = ",".join(next_tickets)

        # blank is changed into "-" in multi line input. so re changed to blank
        self.task_updating_df.loc[self.task_updating_df["Ready_date"] == "-", "Ready_date"] = ""
        self.task_updating_df.loc[self.task_updating_df["Due_date"] == "-", "Due_date"] = ""

        # connect
        self.prj_dfs[self.params.user_name] = self.task_updating_df.combine_first(self.prj_dfs[self.params.user_name]) 
        self.update_tabs()
        sg.popup_no_buttons("new ticket(s) has been added", auto_close=True, auto_close_duration=1)


    # r7 =======================================================================
    def get_memo_items_from_r7(self):
        self.personal_memo["memo"] = self.window["-r7_mul_00-"].get()
        
    def display_memo_item_in_r7_multi(self):
        self.values["-r7_mul_00-"] = self.personal_memo["memo"]
        self.window["-r7_mul_00-"].update(self.personal_memo["memo"])


    # r８ =======================================================================
    def display_info_in_r8_multi(self):
        info = self.create_r8_information()
        self.values["-r8_txt_00-"] = info
        self.window["-r8_txt_00-"].update(info)

    def create_r8_information(self):
        info = []
        info.append(self.window["-r2_txt_02-"].get())
        info.append(r" Begin   ~    End    (Total)   <Break>")
        info.append(self.window["-r2_txt_03-"].get()[5:])
        info.append("")
        aggregate_hours = self.aggregated_daily_project_hours()
        name = ["Project1", "Project2", "Task", "Ticket"]
        for hours_dict, name in zip(aggregate_hours, name):
            info.append(f"◆ hours as per {name}")
            info.append(self.to_str_list_aggregated_hours(hours_dict))
        
        return "\n".join(info)

    def aggregated_daily_project_hours(self):

        date = self.window["-r2_txt_02-"].get()
        name = self.params.user_name
        sch_user = self.sch_dfs[name][date].tolist()[:24*4]

        # aggregate hour as per index
        work_hour = defaultdict(float)
        for idx in sch_user:
            if idx:
                work_hour[idx] += 0.25

        # create keys
        for idx, hour in work_hour.items(): 
            prj1 = f"{self.prj_dfs[name].loc[idx, 'Project1']:<15s} | "
            prj2 = prj1 + f"{self.prj_dfs[name].loc[idx, 'Project2']:<15s} | "
            task = prj2 + f"{self.prj_dfs[name].loc[idx, 'Task']:<15s} | "
            tick = task + f"{self.prj_dfs[name].loc[idx, 'Ticket']:<15s} | "
            work_hour[idx] = [[prj1, prj2, task, tick], hour]

        # aggregate hour as per prj1, 2, task, ticket
        prj1_hour = defaultdict(float)
        prj2_hour = defaultdict(float)
        task_hour = defaultdict(float)
        tick_hour = defaultdict(float)
        for k, hour in work_hour.values():
            prj1_hour[k[0]] += hour
            prj2_hour[k[1]] += hour
            task_hour[k[2]] += hour
            tick_hour[k[3]] += hour

        return prj1_hour, prj2_hour, task_hour, tick_hour


    def to_str_list_aggregated_hours(self, hours_dict):
        prj_hours = []
        prj_hours.extend(f"  {k:<10s}  {v}" for k, v in hours_dict.items())
        prj_hours.append("")
        return "\n".join(prj_hours)


    def log_button_1(self):
        return

    def log_button_2(self):
        return

    def log_button_3(self):
        return


    # r9 =======================================================================
    def add_r9_table_data_into_dfs(self):

        tickets = self.window["-r9_tbl_00-"].get()
        new_tickets_df = []
        if not sg.popup_ok_cancel("add table tickets") == "OK":
            return

        # items = [prj1, prj2, task, ticket_name, estimation, ready_date, due_date]
        # ticket_items = [prj1, prj2, task, ticket, estimation, due_date, status]
        for ticket_items in tickets:
            items = ticket_items[:5] + [""]*2
            items[4] = float(items[4])
            items[6] = "" if ticket_items[5] == "-" else ticket_items[5]
            print(f"{items=}")
            input_df = self._add_tickets_info_into_stored_df(items)
            input_df["Status"] = ticket_items[6]
            new_tickets_df.append(input_df)
            print(input_df["Update_Estimation"])
            print(input_df["Estimation"])
            print(input_df["Due_date"])
        for new_df in new_tickets_df:
            self.prj_dfs[self.params.user_name] = self.prj_dfs[self.params.user_name].append(new_df)
        self.update_tabs()


    def multiline_item_into_table_r9(self):
        tickets, mul_msg = self.parse_multiline_r9()
        self.window["-r9_mul_00-"].update(mul_msg)
        self.window["-r9_tbl_00-"].update(values=tickets)
    
    def parse_multiline_r9(self):
        mul = self.values["-r9_mul_00-"]
        mul = mul.split("\n")
        tickets = []
        msg = []
        for ticket_line in mul:
            if not len(ticket_line):
                continue
            if ticket_line[0] == "#":
                continue
            msg.append(ticket_line)
            t, m = self.ticket_line_to_items(ticket_line)
            if t:
                tickets.append(t)
            if m:
                msg.append(m)
        mul_msg = "\n".join(msg)
        tickets = self.convert_ticket_items(tickets)
        return tickets, mul_msg

    def convert_ticket_items(self, tickets):
        converted_tickets = []
        for ticket_items in tickets:
            ticket_items += [""]*7
            ticket_items[5] = "" if ticket_items[5] == "-" else ticket_items[5]
            ticket_items[6] = ticket_items[6] if ticket_items[6] else "ToDo"
            converted_tickets.append(ticket_items[:7])
        return converted_tickets

    def ticket_line_to_items(self, ticket_line):
        if not ticket_line:
            return None, None
        checker = {0:self.is_prj1_exist, 1:self.is_prj2_exist, 2:self.is_longer_1string, 3:self.is_longer_1string,
                   4:self._can_convert_float025, 5:self.is_correct_due_date_input, 6:self.is_status}
        pos = {0:"Project1", 1:"Project2", 2:"Task", 3:"Ticket", 4:"Estimation hour", 5:"Due date", 6:"Status"}
        ticket_line = ticket_line.split(" ")
        ticket_items = ticket_line[:7]
        for i, item in enumerate(ticket_items):
            if not checker[i](item):
                msg = f"# {pos[i]} is something wrong !"
                return None, msg
        if i < 4:
            return None, "#Prj1, Prj2, Task, Ticket, Estimation hour must be inputted"
        return ticket_items, None

    def is_prj1_exist(self, prj1):
        if prj1 in self.dic_prj1_2.keys():
            self.tmp_prj1 = prj1
            return True
        return False
    
    def is_prj2_exist(self, prj2):
        if prj2 in self.dic_prj1_2[self.tmp_prj1]:
            return True
        return False
    
    def is_longer_1string(self, t):
        if len(t):
            return True
        return False
    
    def is_correct_due_date_input(self, dd):
        if dd == "-" or self._can_convert_datetime(dd):
            return True
        return False

    def is_status(self, status):
        print(f"{self.params.status=}")
        if status in self.params.status:
            return True
        return False

    def write_prj12_to_r9_multi(self):
        mul_msg = ""
        for prj1 in self.dic_prj1_2.keys():
            for prj2 in self.dic_prj1_2[prj1]:
                mul_msg += f"{prj1} {prj2} \n"
        self.window["-r9_mul_00-"].update(mul_msg)
    
    def set_default_r9_multi(self):
        mul_msg = self.values["-r9_mul_00-"]
        mul = mul_msg.split("\n")
        prj1 = None
        for mul_line in mul:
            mul_line = mul_line.split(" ")
            if len(mul_line) < 2:
                continue
            prj1, prj2 = mul_line[:2]
            if prj2 in self.dic_prj1_2.get(prj1, []):
                break
            prj1, prj2 = None, None
        if prj1:
            for dt in self.params.default_task_set:
                mul_msg += f"\n{prj1} {prj2} {dt}"
        else:
            mul_msg += "# clicked samples button. but prj1, prj2 are not inputted\n"
        self.window["-r9_mul_00-"].update(mul_msg)

# ==========================================================================
# internal use functions
#===========================================================================
    def is_every_prj_in_checkbox(self):
        if len(self.hd_cbx_names) < 1:
            return True
        for prj in self.prj:
            if prj in self.hd_cbx_names:
                continue
            return False
        return True

    def set_previous_inputs(self):

        if not self.values["-l3_inp_00-"]:
            self.values["-l3_inp_00-"] = self.personal_memo["set"]["table_query"]
            self.window["-l3_inp_00-"].update(self.personal_memo["set"]["table_query"])
        if not self.values["-l3_inp_01-"]:
            self.values["-l3_inp_01-"] = self.personal_memo["set"]["table_sort"]
            self.window["-l3_inp_01-"].update(self.personal_memo["set"]["table_sort"])

    # calculation =======================================================================
    def _business_days(self, begin, end):
        """counting business days
           include begin date, exclude due date
           ex) form 1/1(Fri) to 1/6(Wed) -> 1/1, 1/4, 1/5 are business date 
               return is 3

        Args:
            begin (datetime.date): begin date
            end (datetime.date): due date

        Returns:
            int : number of business days from begin date to due date
                  due date is not included
        """
        days = (end - begin).days
        begin_week_remain = max(0, 5 - begin.weekday())
        end_week_remain = 5 - max(0, 5 - end.weekday())

        if days <= begin_week_remain:
            return days
        if days - begin_week_remain <= end_week_remain:
            return days - 2
        
        return days - 2 - (days - begin_week_remain - end_week_remain) // 7 * 2

    def _create_temporary_df_for_cal_position(self, df, status):

        tmp_df = df[df["Status"] == status].copy()
        tmp_df["begin_pos"] = 0
        tmp_df["end_pos"] = 0
        tmp_df["over"] = None
        tmp_df["prj"] = tmp_df["Project1"] + "-" + tmp_df["Project2"]
        tmp_df = tmp_df.sort_values("Priority")
        return tmp_df
    

    def _calc_ticket_position(self, tmp_df):
        """
        calculating coordinate of the tickets which is in self.sch_dfs[user] 
        and own status is not "Done"

        Args:
            user (str): selected user name
        """
        time_to_pix = 100 / self.params.hour_in_date
        tmp_pos = 0
        for idx in tmp_df.index:
            tmp_df.loc[idx, "begin_pos"] = tmp_pos
            ticket_hour = max(tmp_df.loc[idx, "Update_Estimation"] - tmp_df.loc[idx, "Man_hour_reg"], 0.5)
            tmp_pos += ticket_hour * time_to_pix
            tmp_df.loc[idx, "end_pos"] = tmp_pos

            # over due date ticket turn on the over flag
            due_date = tmp_df.loc[idx, "Due_date"]
            if due_date:
                tmp_df.loc[idx, "over"] = False
                due_date = datetime.datetime.strptime(due_date, r"%Y/%m/%d").date()
                today = datetime.date.today()
                remaining_days = self._business_days(today, due_date) + 1
                if remaining_days * 100 < tmp_pos:
                    tmp_df.loc[idx, "over"] = True

        return tmp_df


    def _str_to_hash_id(self, item, titles):
        """
        ticket id is generated with hash function from project1, 2, task, ticket and in charge
        """
        item_ids = [i for i, title in enumerate(titles) if title in self.params.hash_item]
        x = "-".join([item[i] for i in item_ids] + [datetime.datetime.now().strftime(r"%S%f")])
        return hashlib.md5(x.encode()).hexdigest()


    def _define_ticket_color(self, project1, project2, task, ds=None):
        if ds:
            project1 = ds["Project1"]
            project2 = ds["Project2"]
            task = ds["Task"]
        x = "-".join([project1, project2, task])
        x = hashlib.md5(x.encode()).hexdigest()
        # c = [w for w in x if w in "0123456789a"]
        # return "".join(["#"] + c[:min(len(c),6)] + ["a"]*max(6-len(c), 0))

        c = ["#", "e", "0", "e", "0", "e", "0"]
        order = [2, 4, 6, 1, 3, 5]
        cnt = 0
        for xi in x:
            if cnt > 5:
                break
            col = order[cnt]
            if cnt < 3:
                if xi in "0123456789abcdef":
                    c[col] = xi
                    cnt += 1
                continue
            if cnt < 6:
                if xi in "abcde":
                    c[col] = xi
                    cnt += 1

        return "".join(c)


    def _priority_update(self, ticket_id=None, step=0, name=None):
        """update priorities of tickets

        Args:
            ticket_id (str, optional): selected ticket id. Defaults to None.
            step (int, optional): priority up down value. Defaults to 0.
            name (str, optional): selected member name. Defaults to None.
            for drawing l1 chart, can update priorities of other member. but cannot save.
        """
        name = name if name else self.params.user_name

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
        pri_df[self.prj_dfs[name]["Status"]==self.params.status[1]] += 99999
        pri_df[self.prj_dfs[name]["Status"]==self.params.status[3]] += 9999
        self.prj_dfs[name]["Priority"] = pri_df
        # sort 
        self.prj_dfs[name] = self.prj_dfs[name].sort_values("Priority")
        # re arrange
        self.prj_dfs[name]["Priority"] = [i+1 for i in range(self.prj_dfs[name].shape[0])]


    def _get_activated_member(self):
        return [name for i, name in enumerate(self.params.team_members) if self.values[f"-hd_rdi_{i:02d}-"]][0]
        

    def _get_is_ticket_and_series_from_ticket_id(self, ticket_id):
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
        user_name = self.params.user_name
        if not sch_row:
            return False
        if sch_col not in self.sch_dfs[user_name].columns.values.tolist():
            self.sch_dfs[user_name][sch_col] = ""
        sch_row = [row + self.params.daily_begin*4 for row in sch_row]
        indices = [f"{(i)//4:02d}:{15*((i)%4):02d}" for i in sch_row]
        self.sch_dfs[user_name].loc[indices, sch_col] = ticket_id
        return True
        
    
    def _warning_not_done_track_record(self):
        """
        If there is a difference between the contents of sch dataframe and trk dataframe
        before today, a warning will be displayed. 
        it is intended to prevent forgetting record
        """
        trk_user = self.trk_dfs[self.params.user_name]
        sch_user = self.sch_dfs[self.params.user_name]
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
            shorter (bool, optional): if true, ask the reason why man hour is shorter than estimation also. Defaults to False.
        """
        name = self.params.user_name
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
            if reason_txt:
                self.prj_dfs[name].loc[ticket_id, "Comment"] = reason_txt
            if reason_txt == None:
                return False
            return True
        return True