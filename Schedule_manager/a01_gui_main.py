# %%==========================================================================
# logging
# ============================================================================
import os
from logging import getLogger, Formatter, StreamHandler, DEBUG, INFO
from logging import handlers

def get_module_logger(module, log_file=r"./log/logging.txt", verbose=False):
    
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = getLogger(module)
    logger = _set_handler(logger, StreamHandler(), False)
    logger = _set_handler(logger, handlers.RotatingFileHandler(log_file, maxBytes=1000000, backupCount=5), verbose)
    logger.setLevel(DEBUG)
    logger.propagate = False
    return logger

def _set_handler(logger, handler, verbose):
    if verbose:
        handler.setLevel(DEBUG)
    else:
        handler.setLevel(INFO)
    handler.setFormatter(Formatter('%(asctime)s %(name)s:%(lineno)s %(funcName)s [%(levelname)s]: %(message)s'))
    logger.addHandler(handler)
    return logger

logger = get_module_logger(__name__, verbose=True)
logger.info('Application starts')
logger.info('logger set')


# %% =======================================================================
logger.debug("import libraries at main file")
#===========================================================================
# default
import os
import datetime
import hashlib

# conda
import pandas as pd
import PySimpleGUI as sg

# user
from b00_schedule_class import ScheduleManage as SchM

# %% =======================================================================
# pysimple gui settings
#===========================================================================
# window layout is defined in b01_schedule_class_base
# button or other functions are defined in b01_schedule_class
sch_m = SchM(logger)
sch_m.create_window()
sch_m.window.read(timeout=1)

# %% =======================================================================
# simple gyi while
#===========================================================================
# Event Loop to process "events" and get the "values" of the inputs
last_update_time = datetime.datetime.now()

def gui_main(sch_m):

    event, pos, item, eid = sch_m.parse_event()
    if event and "MV" not in event:
        sch_m.log("debug", event)

    if event == sg.WIN_CLOSED: # if user closes window or clicks cancel
        return False

    if event == "Cs-":
        sch_m.save_files()
    if event == "Cr-":
        sch_m.reload_files()
        sch_m.update_tabs()
    if event == "CR-":
        sch_m.save_files()
        sch_m.reload_files()
        sch_m.update_tabs()

    # if event == "CW-":
    #     print("cw")

    # %% =======================================================================
    # header
    #===========================================================================
    if pos == "hd":  # header
        if item == "btn":  # click button
            if eid == 0: # all
                sch_m.activate_all_header_buttons()
                sch_m.show_prj_boxes_as_chk_box()
            if eid == 1: # clear
                sch_m.deactivate_all_header_buttons()
                sch_m.show_prj_boxes_as_chk_box()
            if eid == 2: # draw chart
                sch_m.update_tabs()
            if eid == 3: # upload
                sch_m.save_files()
            if eid == 4: # download
                sch_m.reload_files()
                sch_m.update_tabs()

        if item == "cbx":  # check box was updated
            sch_m.show_prj_boxes_as_chk_box([eid])

        if item == "rdi":  # radio button
            sch_m.update_tabs()

        return True

    # %% =======================================================================
    # left tab
    #===========================================================================
    if pos == "l0":
        if item == "btn":
            if eid == 0:
                sch_m.save_settings_and_restart_app()
                sch_m._initialize()
                sch_m.window.close()
                sch_m.create_window()

    if pos == "lt":
        if item == "grp":
            sch_m.l1_chart_draw()
        return True

    if pos == "l1":  # left tab1
        if item == "btn":
            if eid == 0:
                sch_m.shrink_l1_chart()
            if eid == 1:
                sch_m.enlarge_l1_chart()
            if eid in [2, 3]:
                pm = eid*2 - 5
                sch_m.change_font_size(pm)
        if item == "cbx":
            sch_m.l1_chart_draw()
        if item[:3] == "grp":
            if item == "grp" or item == "grp2":
                sch_m.schedule_ticket_to_daily_table()
            if "MV" in item:
                ticket_id = sch_m.get_and_remain_mouse_on_ticket_id(item, eid)
                if ticket_id:
                    flag_is_ticket, mouse_on_prj = sch_m._get_is_ticket_and_series_from_ticket_id(ticket_id)
                    if flag_is_ticket:
                        sch_m.display_values_in_df_to_r1(mouse_on_prj)
                        sch_m.display_values_in_df_to_r6(mouse_on_prj)
            if "RC" in item:
                sch_m.process_l1_right_click_menu(event, eid)
        return True

    if pos == "l2":  # left tab2
        return True

    if pos == "l3":  # left tab2
        if item == "btn":
            if eid < 4:
                sch_m.update_priority_as_per_button_pressed(eid)
            if eid == 4:
                sch_m.calculate_priority()
                sch_m.display_l3_table_as_multiline_command()
            if eid == 20:
                sch_m.display_l3_table_as_multiline_command()
        if "tbl" in item:
            sch_m.l3_table_selected_ticket_changed()
        return True

    if pos == "l4":
        if item == "btn":
            if eid == 0:
                sch_m.accept_order()
            if eid == 1:
                sch_m.deny_order()
        return True

    if pos == "l5":
        if item == "btn":
            if eid == 0:
                sch_m.delete_follow_ticket()
        return True

    # %% =======================================================================
    # right tab
    #===========================================================================
    if pos == "rt":
        if item == "grp":
            sch_m.set_right_click_menu_of_daily_table()
            sch_m.update_tabs()
    
    if pos == "r1":  # right tab1 -plan
        if item[:3] == "inp":
            if len(item) == 6:
                if item[4:6] == "LC":
                    sch_m.select_date_for_date_box(eid)
            sch_m.set_color_of_boxes_inputted_invalid_value_r1()
            sch_m.set_right_click_menu_of_prj12_task()
            # sch_m._r1_pre_next_ticket_table_update()
        if item[:3] == "btn":
            if eid == 0:
                sch_m.create_ticket_as_r1()
            if eid == 1:
                sch_m.update_ticket_as_r1()
            if eid == 2:
                sch_m.delete_ticket_as_r1()
        if item == "right_menu":
            sch_m.input_prj12_and_task_by_right_click(event)
            sch_m.set_right_click_menu_of_prj12_task()
        if item == "right_menu_tbl":
            sch_m.delete_ticket_from_prev_next_table(eid)
        return True

    if pos == "r2":  # right tab2 -daily
        if item == "btn":
            # if eid == 0:
            #     sch_m.r2_save_plan_button_pressed()
            if eid == 1:
                sch_m.record_daily_table_items()
            if eid == 2:
                sch_m.r2_get_schedule_from_app_button_pressed()
            if eid == 4:
                sch_m.delete_items_from_daily_table()
            if eid in [10, 11, 12]:
                sch_m.daily_table_date_move_to_before_after(eid)
        if item == "txt":
            if eid == 2:
                sch_m.select_date_of_daily_table()
        if item == "inp":
            sch_m.got_r2_information_data()
            sch_m.display_team_box()
        if item == "right_menu":
            sch_m.set_daily_row_as_per_right_click(eid)
        if item == "tbl-DR":
            sch_m.select_r2_table_rows_with_mouse_drag()
        # if item == "tbl-BP":
        #     sch_m.select_r2_table_rows_with_mouse_click()
        if item == "tbl-BR":
            sch_m.r2_table_start_release()
        return True

    if pos == "r3":  # right tab3 -team
        if item == "btn":
            if eid == 0:
                sch_m.r3_mail_button_pressed()
            if eid == 1:
                sch_m.r3_folder_button_pressed()
            if eid == 2:
                sch_m.r3_memo_button_pressed()
        return True

    if pos == "r4":  # right tab4 -fever
        return True

    if pos == "r5":  # right tab5 -plan
        if item == "btn":
            sch_m.change_displayed_plan_on_multiline(eid)
            sch_m.display_plans_on_multiline()
        if item == "mul":
            sch_m.got_plans_from_multiline(eid)
        return True

    if pos == "r6":  # right tab6 -task
        if item == "inp":
            sch_m.set_color_of_boxes_inputted_invalid_value_r6()
            sch_m.set_right_click_menu_of_prj12_task()
        if item[:4] == "btn1":
            if eid == 0:
                sch_m.add_r6_table_data_into_dfs()
            if eid == 1:
                sch_m.display_tickets_in_table_r6()
        if item[:4] == "btn2":
            if eid <= 1:
                # 順番入れ替え機能の要望があれば追加する
                return True
            if eid <= 2:
                sch_m.table_items_into_multiline_r6()
                return True
            if eid == 3:
                sch_m.multiline_item_into_table_r6()
                return True

    if pos == "r7":  # right tab7 -memo
        if item == "mul":
            sch_m.get_memo_items_from_r7()
        return True

    if pos == "r8":  # right tab8 -log
        if item == "btn":
            if eid == 0:
                sch_m.display_info_in_r8_multi()
            if eid == 1:
                sch_m.log_button_1()
            if eid == 2:
                sch_m.log_button_2()
            if eid == 3:
                sch_m.log_button_3()
        return True

    if pos == "r9":
        if item == "btn":
            if eid == 0:
                sch_m.add_r9_table_data_into_dfs()
            if eid == 1:
                sch_m.multiline_item_into_table_r9()
            if eid == 2:
                sch_m.write_prj12_to_r9_multi()
            if eid == 3:
                sch_m.set_default_r9_multi()

    return True


flag = True
while flag:
    try:
        flag = gui_main(sch_m)
    except Exception as e:
        flag = False
        logger.exception("main loop")
        # sg.popup_ok(f"Error!!! {e} close application. sorry.")

logger.info("window_close")
sch_m.window.close()

