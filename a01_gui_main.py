# %% =======================================================================
# import libraries
#===========================================================================
# default
import os
import datetime
import hashlib

# conda
import pandas as pd
import PySimpleGUI as sg  

# user
from b01_schedule_class_base import ScheduleManageBase
from b01_schedule_class import ScheduleManage

# %% =======================================================================
# pysimple gui settings
#===========================================================================
# window layout is defined in b01_schedule_class_base
# button or other functions are difined in b01_schedule_class
sch_m = ScheduleManage()
sch_m.create_window()
sch_m.window.read(timeout=1)

# %% =======================================================================
# simple gyi while
#===========================================================================
# Event Loop to process "events" and get the "values" of the inputs
while True:

    event, pos, item, eid = sch_m.parse_event()
    # if event and "MV" not in event:
    #     print(event, pos, item, eid)

    if event == sg.WIN_CLOSED: # if user closes window or clicks cancel
        break

    # %% =======================================================================
    # header
    #===========================================================================
    if pos == "hd":  # header
        if item == "btn":  # click button
            if eid == 0: # all
                sch_m.header_all_button_pressed()
                sch_m.header_checkbox_changed()
            if eid == 1: # clear
                sch_m.header_clear_button_pressed()
                sch_m.header_checkbox_changed()
            if eid == 2: # drawchart
                sch_m.header_refresh_button_pressed()
            if eid == 3: # upload
                sch_m.header_upload_button_pressed()
            if eid == 4: # download
                sch_m.header_reload_button_pressed()

        if item == "cbx":  # check box was updated
            sch_m.header_checkbox_changed([eid])

        if item == "rdi":  # radio button
            sch_m.header_member_raido_button_changed()

        continue

    # %% =======================================================================
    # left tab
    #===========================================================================
    if pos == "lt":
        if item == "grp":
            sch_m.l1_chart_draw()
        continue

    if pos == "l1":  # left tab1
        if item[:3] == "grp":
            if len(item) == 3:
                sch_m.l1_graph_area_clicked()
            if "MV" in item:
                sch_m.l1_graphs_capture_mouse_motion(eid)
            if "RC" in item:
                sch_m.l1_graph_right_click_menu_selected(event, eid)
        continue

    if pos == "l2":  # left tab2
        continue

    if pos == "l3":  # left tab2
        if item == "btn":
            if eid < 4:
                sch_m.l3_priority_updown_button_pressed(eid)
            if eid == 4:
                sch_m.l3_priority_auto_button_pressed()
        if "tbl" in item:
            sch_m.l3_table_selected_ticket_changed()
        continue

    if pos == "l0":
        if item == "btn":
            if eid == 0:
                sch_m.l0_settings_save_and_restart_button_pressed()

    # %% =======================================================================
    # right tab
    #===========================================================================
    if pos == "r1":  # right tab1
        if item[:3] == "inp":
            if len(item) == 6:
                if item[4:6] == "LC":
                    sch_m.r1_input_date_box_selected(eid)
            sch_m.r1_input_check()
            # sch_m._r1_pre_next_ticket_table_update()
        if item[:3] == "btn":
            if eid == 0:
                sch_m.r1_apply_button_pressed()
            if eid == 1:
                sch_m.r1_delete_button_pressed()
        if item == "right_menu":
            sch_m.r1_right_click_menu_clicked(event)
        continue

    if pos == "r2":  # right tab2
        if item == "btn":
            # if eid == 0:
            #     sch_m.r2_save_plan_button_pressed()
            if eid == 1:
                sch_m.r2_save_record_button_pressed()
            if eid == 4:
                sch_m.r2_delete_button_pressed()
        if item == "txt":
            if eid == 2:
                sch_m.r2_date_txt_pressed()
        if item == "inp":
                sch_m.r2_information_box_inputed()
        continue
    if pos == "r3":  # right tab3
        if item == "btn":
            if eid == 0:
                sch_m.r3_mail_button_pressed()
            if eid == 1:
                sch_m.r3_folder_button_pressed()
            if eid == 2:
                sch_m.r3_memo_button_pressed()
            
        continue
    if pos == "r4":  # right tab4
        continue
    if pos == "r5":  # right tab5
        if item == "btn":
            sch_m.r5_arrow_button_pressed(eid)
        if item == "mul":
            sch_m.r5_df_from_multiline(eid)

sch_m.window.close()

