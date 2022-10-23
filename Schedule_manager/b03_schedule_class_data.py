# %% =======================================================================
# import libraries
#===========================================================================
from dataclasses import dataclass, asdict, field
from typing import List

# %% =======================================================================
# class
#===========================================================================
@dataclass
class SettingParameters:

    window_theme : str = "DarkGrey4"
    header_num_row : int = 4
    user_name : str = "がんばる上司"
    hour_in_date : int = 6
    daily_table_rows : int = 80
    daily_begin : int = 7
    daily_table_display_rows : int = 50
    font : str = "Meiryo"
    font_size : int = 10
    team_members : List[str] = field(default_factory=lambda: ["できる社員", "すごい社員", "がんばる上司"])
    auto_priority_activate : bool = True

    columns : List[str] = field(default_factory=lambda:[
                                 "Project1", "Project2", "Task", "Ticket", "Detail", "Is_Task",
                                 "Ready_date", "Due_date", "Estimation", "Update_Estimation",
                                 "In_charge",
                                 "Prev_task", "Next_task",
                                 "Status",
                                 "Begin_date_reg", "End_date_reg", "Man_hour_reg",
                                 "File_path", "Comment",
                                 "Priority",
                                 "Color",
                                 ])
    not_updatable_columns : List[str] = field(
        default_factory=lambda:["Is_Task", "In_charge", "Begin_date_reg", "End_date_reg", "Man_hour_reg", "Priority"])
    hash_item : List[str] = field(
        default_factory=lambda:["Project1", "Project2", "Task", "Ticket", "In_charge"])
    priority_list : List[str] = field(
        default_factory=lambda:["Project1", "Project2", "Task", "Ticket", "In_charge", "Ready_date", "Due_date", "Status", "Update_Estimation", "End_date_reg", "Man_hour_reg", "Priority", "Index"])
    schedule_add_info : List[str] = field(
        default_factory=lambda:["Hour", "Health", "Safety", "Reasons_overwork", "Information", "Memo1", "Memo2", "Memo3"])
    status : List[str] = field(
        default_factory=lambda:["ToDo", "Done", "Pending", "Often"])
    ticket_maker_table : List[str] = field(
        default_factory=lambda:["Ticket", "Estimation", "Man_hour_reg", "Ready_date", "Due_date"])



@dataclass
class GUISize:

    window_w : int = 1600
    window_h : int = 1000
    header_button_w : int = 10
    header_button_h : int = 1
    header_chk_box_w : int = 20
    header_chk_box_h : int = 1
    header_radio_w : int = 15
    header_radio_h : int = 1
    right_button_w : int = 10
    right_button_h : int = 1
    right_input_w : int = 15
    right_input_h : int = 1
    right_comment_boxes_w : int = 4800
    right_comment_boxes_h : int = 100
    right_team_box_w : int = 60
    right_team_box_h : int =  30
    graph_top_right_w : int = 10000
    graph_top_right_h : int = 100
    left3_col_width_w : int = 12
    left3_col_width_h : int = 0
    r1_table_width : int = 20
    r2_table_width_1 : int = 30
    r2_table_width_2 : int = 8
    r2_table_width_3 : int = 20
    tbl_row_hight : int = 12
    often_width : int = 200

    header_clm_chk_w = window_w // 20 * 12
    header_clm_chk_h = window_h // 20 * 2
    header_clm_btn_w = window_w // 20 * 1
    header_clm_btn_h = window_h // 20 * 2
    header_clm_rdi_w = window_w // 20 * 4
    header_clm_rdi_h = window_h // 20 * 2
    left_tab_group_w = window_w // 20 * 14
    left_tab_group_h = window_h // 20 * 18
    left_tab1_canvas_w = left_tab_group_w*10
    left_tab1_canvas_h = left_tab_group_h// 20 *  2
    right_tab_group_w = window_w // 20 * 6
    right_tab_group_h =window_h // 20 * 18


@dataclass
class WindowTheme:

    use_user_setting : bool = False
    background : str = "#9e9e8e"
    text : str = '#FFCC66'
    input_box : str = '#339966'
    text_input : str = '#000000'
    text_table : str = '#aa0000'
    table_background : str = "#9e9e8e"
    scroll : str = '#99CC99'
    button_normal : str = '#FFCC66'
    button_pressed : str = '#003333'
    progress_1 : str = '#D1826B'
    progress_2 : str = '#CC8019'
    warning : str = "#aaaa00"
    alert : str = "#9f4040"
    graph_background : str = "#7f7f7f"
    graph_line : str = "#eeeeee"
    graph_vertical_line : str = "#8f8f8f"
    graph_text : str = "#eeeeee"
    graph_unknown : str = "#505050"
    schedule_table1 : str = "#888888"
    schedule_table2 : str = "#808080"
    schedule_table3 : str = "#787878"
    schedule_table4 : str = "#707070"
    table_ticket_done : str = "#303030"
    table_ticket_often : str = "#404040"
    table_ticket_other : str = "#505050"
    order_ticket_someone : str = "#444444"
    order_ticket_mine : str = "#dd4040"
    follow_ticket_deleted : str = "#883333"
    follow_ticket_to_be_approved : str = "#228888"
    follow_ticket_todo : str = "#228833"
    follow_ticket_done : str = "#223388"
    follow_ticket_other : str = "#444444"
    border : int = 1
    slider_depth : int = 0
    progress_depth : int = 0