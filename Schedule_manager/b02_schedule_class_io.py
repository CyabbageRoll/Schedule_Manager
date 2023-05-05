# %% =======================================================================
# import libraries
#===========================================================================
# default
import os
import glob
import json
import datetime
import pickle
from collections import defaultdict 
from distutils.util import strtobool

# pip or conda install
import pandas as pd
import PySimpleGUI as sg

# user
from b03_schedule_class_data import SettingParameters, GUISize, WindowTheme

# %% =======================================================================
# class
#===========================================================================

class ScheduleManageIO:

    def _read_settings_file(self):
        """read setting values from sch_m_setting.csv file.
           1. a directory where dataframe files save -> self.prj/sch/trk_file
           2. parameters of font, num of table of rows...etc -> self.param
           3. values of gui size -> self.sizes

        Returns:
            str or bool False
               : if some essential key was not defined in csv file
                 return the key value, else, return False
        """

        self.logger.info("read setting file")
        if not os.path.exists(self.setting_file):
            return "settings file is not existed"
        with open(self.setting_file, encoding="UTF-8") as f:
            settings = json.load(f)
        
        root_dir  = settings["file_save_dir"]
        self.params = SettingParameters(**settings["param"])
        self.sizes = GUISize(**settings["size"])
        self.theme = WindowTheme(**settings["window_theme"])

        self.prj_file = os.path.join(root_dir, r"prj/prj_file_--name--.pkl")
        self.sch_file = os.path.join(root_dir, r"sch/sch_file_--name--.pkl")
        self.trk_file = os.path.join(root_dir, r"trk/trk_file_--name--.pkl")
        self.pln_file = os.path.join(root_dir, r"pln/pln_file_--name--.pkl")
        self.ord_file = os.path.join(root_dir, r"ord/--name--_--index--.pkl")
        self.backup_dir_save = os.path.join(root_dir, "backup")
        self.backup_dir_local = r"./backup"

        return None


    def _save_backup_process(self, file_dir, file_name, obj, backups=5):
        
        os.makedirs(file_dir, exist_ok=True)
        file_name_pre = datetime.datetime.strftime(datetime.datetime.now(), r"%y%m%d%H_")
        new_file_path = os.path.join(file_dir, file_name_pre + file_name)

        files = glob.glob(os.path.join(file_dir, "*.pkl"))
        files = [file for file in files if file_name in file]
        if len(files) > backups:
            files.sort()
            if files[-1] != new_file_path:
                os.remove(files[0])

        with open(new_file_path, mode="wb") as f:
            pickle.dump(obj, f)


    def _save_backup_file(self, obj, file_name):
        file_name += f"_file_{self.params.user_name}.pkl"
        self._save_backup_process(self.backup_dir_save, file_name, obj, backups=3)
        if self.params.back_up_at_local:
            self._save_backup_process(self.backup_dir_local, file_name, obj, backups=10)


    def save_files(self, popup=True):
        """save prj, sch, trk dataframe(s) at user specified location"""
        self.logger.info("save_files start")
        self._save_prj_file()
        self._save_daily_schedule_file()
        self._save_man_hour_tracker_file()
        self._save_monthly_plan_file()
        self._save_personal_memo()
        if popup:
            sg.popup_no_buttons("Saved", auto_close=True, auto_close_duration=0.5)
        self.logger.info("save_files done")

    def reload_files(self, popup=True):
        """read prj, sch, trk dataframe(s) from user specified location"""
        self.logger.info("reload_files start")
        self._read_prj_file()
        self._read_daily_schedule_file()
        self._read_man_hour_tracker_file()
        self._read_monthly_plan_file()
        self.read_order()
        self.read_personal_memo()
        if popup:
            sg.popup_no_buttons("Loaded", auto_close=True, auto_close_duration=0.5)
        if not self.is_every_prj_in_checkbox():
            sg.popup_no_buttons("restart window due to updating header checkboxes", auto_close=True, auto_close_duration=1)
            self.window.close()
            self.create_window()
        self.logger.info("reload_files done")
    

    def save_settings_and_restart_app(self):
        # TODO : Need to be updated setting tab and button
        settings_list = [self.SETTINGS_DIR, self.SETTINGS_PARAM, self.SETTINGS_SIZE]
        setting_type_list = [self.SETTINGS_DIR_TYPE, self.SETTINGS_PARAM_TYPE, self.SETTINGS_SIZE_TYPE]

        for settings, setting_type in zip(settings_list, setting_type_list):
            for setting, input_type in zip(settings, setting_type):  
                for col, t in enumerate(input_type):
                    self.df_settings.loc[setting, col + 1] = self.values[f"-{setting}_{col:02d}-"]

        self.df_settings.to_csv("./sch_m_settings.csv", header=None)
        self.save_files()

        return


    def _read_prj_file(self):
        """ 
         reading each member's prj file
        self.prj_dfs (project DataFrames) is dictionary
        {keys are member name : values are each member's dataframe}
         If prj file is not exist, create new dataframe. 
        it has initial tickets ("one off work" and "regularly work")
         After read all prj files, create dictionaries "dic_prj1_2" and "dic_prj_task"
        "dic_prj1_2" -> key is project 1, values are project 2 
        "dic_prj1_task" -> key is combined project1 and project 2, values are task. 
        these dictionaries are used for checking input box of r1 (ticket create) and creating self.prj
        """
        self.prj_dfs = {}
        for name in self.params.team_members:
            file_name = self.prj_file.replace("--name--", name)
            if os.path.isfile(file_name):
                self.prj_dfs[name] = pd.read_pickle(file_name)
                continue
            items = []
            items.append(["Other", "Other", "task", "sample-ticket", "", False, "", "", 2, 2, name, "", "", self.params.status[0], "", "", 0, "", "", 0, "6a1a57"])
            indices = [self._str_to_hash_id(item, self.params.columns) for item in items]
            self.prj_dfs[name] = pd.DataFrame(items, columns=self.params.columns, index=indices)

        # get project 1&2 title for check box and check new ticket
        self.dic_prj1_2 = defaultdict(set)
        self.dic_prj_task = defaultdict(set)
        for df in self.prj_dfs.values():
            for item in df.itertuples(name=None):
                prj = "-".join(item[1:3])
                self.dic_prj1_2[item[1]].add(item[2])
                self.dic_prj_task[prj].add(item[3])
        self.prj = sorted(list(self.dic_prj_task.keys()))


    def _save_prj_file(self):
        file_name = self.prj_file.replace("--name--", self.params.user_name)
        self.prj_dfs[self.params.user_name].to_pickle(file_name)
        self._save_backup_file(self.prj_dfs[self.params.user_name], "prj")

    def _read_daily_schedule_file(self):
        self.sch_dfs = {}
        for name in self.params.team_members:
            file_name = self.sch_file.replace("--name--", name)
            if os.path.isfile(file_name):
                self.sch_dfs[name] = pd.read_pickle(file_name)
            else:
                indices = [f"{i//4:02d}:{15*(i%4):02d}" for i in range(24*4)] + self.params.schedule_add_info
                self.sch_dfs[name] = pd.DataFrame(columns=[], index=indices)


    def _save_daily_schedule_file(self):
        file_name = self.sch_file.replace("--name--", self.params.user_name)
        dir_path, _ = os.path.split(file_name)
        if not os.path.isdir(dir_path):
            ret = sg.popup_ok_cancel(f"{dir_path} is not exist. Create this directory(ies) ?")
            if ret != "OK":
                return
            os.makedirs(dir_path) 
        self.sch_dfs[self.params.user_name].to_pickle(file_name)
        self._save_backup_file(self.sch_dfs[self.params.user_name], "sch")


    def _read_man_hour_tracker_file(self):
        self.trk_dfs = {}
        for name in self.params.team_members:
            file_name = self.trk_file.replace("--name--", name)
            if os.path.isfile(file_name):
                self.trk_dfs[name] = pd.read_pickle(file_name)
            else:
                indices = self.prj_dfs[self.params.user_name].index.values.tolist()
                self.trk_dfs[name] = pd.DataFrame(columns=[], index=indices)


    def _save_man_hour_tracker_file(self):
        file_name = self.trk_file.replace("--name--", self.params.user_name)
        dir_path, _ = os.path.split(file_name)
        if not os.path.isdir(dir_path):
            ret = sg.popup_ok_cancel(f"{dir_path} is not exist. Create this directory(ies) ?")
            if ret != "OK":
                return
            os.makedirs(dir_path)
        self.trk_dfs[self.params.user_name].to_pickle(file_name)
        self._save_backup_file(self.trk_dfs[self.params.user_name], "trk")

    def _read_monthly_plan_file(self):
        self.pln_dfs = {}
        for name in self.params.team_members:
            file_name = self.pln_file.replace("--name--", name)
            if os.path.isfile(file_name):
                self.pln_dfs[name] = pd.read_pickle(file_name)
                if "week5" not in self.pln_dfs[name].index:
                    values = [""] * len(self.pln_dfs[name].columns)
                    self.pln_dfs[name].loc["week5"] = values

            else:
                indices = ["month", "week1", "week2", "week3", "week4", "week5"]
                self.pln_dfs[name] = pd.DataFrame(columns=[], index=indices)


    def _save_monthly_plan_file(self):
        file_name = self.pln_file.replace("--name--", self.params.user_name)
        dir_path, _ = os.path.split(file_name)
        if not os.path.isdir(dir_path):
            ret = sg.popup_ok_cancel(f"{dir_path} is not exist. Create this directory(ies) ?")
            if ret != "OK":
                return
            os.makedirs(dir_path)
        self.pln_dfs[self.params.user_name].to_pickle(file_name)
        self._save_backup_file(self.pln_dfs[self.params.user_name], "pln")


    def _save_order(self, input_df):
        file_name = self.ord_file.replace("--name--", self.params.user_name)
        file_name = file_name.replace("--index--", input_df.index[0])
        dir_path, _ = os.path.split(file_name)
        if not os.path.isdir(dir_path):
            ret = sg.popup_ok_cancel(f"{dir_path} is not exist. Create this directory(ies) ?")
            if ret != "OK":
                return
            os.makedirs(dir_path)
        input_df.to_pickle(file_name)


    def read_order(self):
        dir_path, _ = os.path.split(self.ord_file)
        order_files = glob.glob(os.path.join(dir_path, "*.pkl"))

        self.order_dic = {}
        for file in order_files:
            file_name = os.path.split(file)[1]
            maker, idx = file_name.split("_")
            idx = idx[:-4]
            self.order_dic[idx] = [maker, pd.read_pickle(file)]

        if not len(self.order_dic):
            items = ["", "", "", "None-ticket", "", False, "", "", 2, 2, "None", "", "", self.params.status[0], "", "", 0, "", "", 0, "6a1a57"]
            index = "temporary-id"
            self.order_dic[index] = ["administrator", pd.DataFrame([items], columns=self.params.columns, index=[index])]
            # df = self.order_dic[index][1]


    def _save_personal_memo(self):
        with open(self.memo_file, 'w', encoding="UTF-8") as f:
            json.dump(self.personal_memo, f, indent=4, ensure_ascii=False)


    def read_personal_memo(self):
        if not os.path.exists(self.memo_file):
            return
        with open(self.memo_file, encoding="UTF-8") as f:
            memo = json.load(f)
        for k, v in memo.items():
            if k in self.personal_memo.keys():
                self.personal_memo[k] = v
