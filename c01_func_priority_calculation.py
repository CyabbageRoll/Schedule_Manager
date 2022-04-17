
# %% =======================================================================
# import 
#===========================================================================
import datetime
from heapq import heapify, heappush, heappop

import pandas as pd

# %% =======================================================================
# Union Find
#===========================================================================

class UnionFind():
    def __init__(self, max_size:int):
        self.parents = [-1] * max_size

    def root(self, id):
        if self.parents[id] < 0:
            return id
        self.parents[id] = self.root(self.parents[id])
        return self.parents[id]

    def linking(self, id1, id2):
        id1 = self.root(id1)
        id2 = self.root(id2)
        if id1 == id2:
            return
        if self.parents[id1] > self.parents[id2]:
            id1, id2 = id2, id1

        self.parents[id1] += self.parents[id2]
        self.parents[id2] = id1


# %% =======================================================================
# sort
#===========================================================================

class SortTickets:

    def __init__(self, df, hour_in_date):

        # self.df = df.sort_values("Priority")
        self.df = df.copy()
        self.num_tickets = df.shape[0]
        self.t2n = {}          # ticket id to number
        self.n2t = {}          # number to ticket id
        self.num_groups = 0
        self.groups = {}
        self.groups_sorted = {}
        self.hours = 6

    def calc_priority(self):
        self._create_ticket_id_and_number_dic()
        self._make_flow_dict_and_count_in_out()
        self._date_to_hours()
        self._calc_begin_limit_hour()
        self._topo_sort_from_front()


    def _create_ticket_id_and_number_dic(self):
        """create two dictionaries. one is ticket id to number id 
        and the other more is a reversed.
        - ticket id : dataframe ticket hash id. dataframe index.
        - number id : number ordered from top of dataframe. dataframe iloc.
        """
        for nid, tid in enumerate(self.df.index.tolist()):
            self.t2n[tid] = nid   # nid is used as number id
            self.n2t[nid] = tid   # tid is used as ticket id
        

    def _grouping_tickets(self):
        """not use
        """
        uf = UnionFind(self.num_tickets)
        for i in range(self.num_tickets):
            # get next ticket(s) of each ticket and convert to number id to handle with Union Find
            next_tickets = [self.t2n[tid] for tid in self.df.iloc[i]["Next_task"].split(",") if tid]
            for nid in next_tickets:
                uf.linking(i, nid)

        for i, p in enumerate(uf.parents):
            if p < 0: # parent
                self.num_groups += 1
                gid = i
            else:
                gid = uf.root(p)
            if gid in self.groups:
                self.groups[gid].append(i)
            else:
                self.groups[gid] = [i]


    def _make_flow_dict_and_count_in_out(self):
        # counting in flow ids for topological sort
        self.tids = self.df.index.values.tolist()
        self.out_ids, self.in_ids = {}, {}
        self.num_ins = {tid : 0 for tid in self.tids}
        self.num_outs = {tid : 0 for tid in self.tids}

        for tid in self.tids:
            next_tickets = [t for t in self.df.loc[tid, "Next_task"].split(",") if t]
            prev_tickets = [t for t in self.df.loc[tid, "Prev_task"].split(",") if t]
            
            # remove myself and not existing id (that task was removed or already done)
            remove_tickets = []
            for next_ticket in next_tickets:
                if next_ticket == tid:
                    remove_tickets.append(next_ticket)
                if next_ticket not in self.tids:
                    remove_tickets.append(next_ticket)
            for remove_ticket in remove_tickets:
                next_tickets.remove(remove_ticket)

            remove_tickets = []
            for prev_ticket in prev_tickets:
                if prev_ticket == tid:
                    remove_tickets.append(prev_ticket)
                if prev_ticket not in self.tids:
                    remove_tickets.append(prev_ticket)
            for remove_ticket in remove_tickets:
                prev_tickets.remove(remove_ticket)
            
            self.out_ids[tid] = next_tickets
            self.in_ids[tid] = prev_tickets
            for next_tid in next_tickets:
                self.num_ins[next_tid] += 1
            for prev_tid in prev_tickets:
                self.num_outs[prev_tid] += 1


    def _ticket_id_to_ticket_name(self, tid):
        return self.df.loc[tid, "Ticket"]

    def _date_to_hours(self):

        self.due_hour = {tid : 9999 for tid in self.tids}
        self.due_date = {tid : None for tid in self.tids}
        self.ready_hour = {tid : 0 for tid in self.tids}
        self.ready_date = {tid : None for tid in self.tids}
        begin_date = datetime.date.today()
        for tid in self.tids:
            dd = self.df.loc[tid, "Due_date"]
            if dd:
                due_date = datetime.date(*[int(ymd) for ymd in dd.split("/")])
                self.due_date[tid] = due_date
                self.due_hour[tid] = self._business_days(begin_date, due_date) * self.hours
            rd = self.df.loc[tid, "Ready_date"]
            if rd:
                ready_date = datetime.date(*[int(ymd) for ymd in rd.split("/")])
                self.ready_date[tid] = ready_date
                self.ready_hour[tid] = self._business_days(begin_date, ready_date) * self.hours


    def _business_days(self, begin, end):
        """counting business days
           include begin date, exclude due date
           ex) form 1/1(Fri) to 1/6(Wed) -> 1/1, 1/4, 1/5 are business date 
               retunr is 3

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


    def _calc_begin_limit_hour(self):
        # topo_sort_from_behind
        end_ids = [tid for tid in self.tids if not self.num_outs[tid]]
        self.begin_limit = {tid:9999 for tid in self.tids}

        while end_ids:
            tid = end_ids.pop()
            due_hour = min(self.due_hour[tid], self.begin_limit[tid])
            self.begin_limit[tid] = due_hour - self.df.loc[tid, "Update_Estimation"]
            for prev_tid in self.in_ids[tid]:
                if self.begin_limit[prev_tid] > 9990:
                    self.begin_limit[prev_tid] = self.begin_limit[tid]
                else:
                    self.begin_limit[prev_tid] -= self.df.loc[tid, "Update_Estimation"]
                self.num_outs[prev_tid] -= 1
                if self.num_outs[prev_tid] == 0:
                    end_ids.append(prev_tid)


    def _topo_sort_from_front(self):

        def try_again(tip_ids, waiting_tid, wait_hour):
            for wt in waiting_tid:
                heappush(tip_ids, wt)
            return tip_ids, [], min(wait_hour), []

        self.tid_pos = {tid:[] for tid in self.tids} 
        tip_ids = [tid for tid in self.tids if not self.num_ins[tid]]
        tip_ids = [[max(self.begin_limit[tid], self.ready_hour[tid]), tid] for tid in tip_ids]
        heapify(tip_ids)
        hour_begin = 0
        self.sorted_tid = []
        waiting_tid = []
        wait_hour = []

        while tip_ids:
            begin_limit, tid = heappop(tip_ids)

            # can not start tid ticket beacuse it has not been ready on
            if hour_begin < self.ready_hour[tid]:  # can not start tid
                waiting_tid.append([begin_limit, tid])
                wait_hour.append(self.ready_hour[tid])
                if not tip_ids:
                    tip_ids, waiting_tid, hour_begin, wait_hour = try_again(tip_ids, waiting_tid, wait_hour)
                continue
            
            # if waiting tid exist, this tid can be schedule as long as finished before wait_hour
            if waiting_tid:
                if hour_begin + self.df.loc[tid, "Update_Estimation"] > max(wait_hour):
                    waiting_tid.append([begin_limit, tid])
                    if not tip_ids:    
                        tip_ids, waiting_tid, hour_begin, wait_hour = try_again(tip_ids, waiting_tid, wait_hour)
                    continue

            hour_end = hour_begin + self.df.loc[tid, "Update_Estimation"]
            self.tid_pos[tid] = [hour_begin, hour_end]
            for next_tid in self.out_ids[tid]:
                self.num_ins[next_tid] -= 1
                if self.num_ins[next_tid] == 0:
                    heappush(tip_ids, [max(self.begin_limit[next_tid], self.ready_hour[next_tid]), next_tid])
            
            if waiting_tid:
                for wt in waiting_tid:
                    heappush(tip_ids, wt)
                waiting_tid = []
                wait_hour = []

            self.sorted_tid.append(tid)
            hour_begin = hour_end


if __name__ == "__main__":

    # %% =======================================================================
    # test case
    #===========================================================================
    import hashlib

    def str_to_hash_id(item, titles):
        use_items = ["Project1", "Project2", "Task", "Ticket", "In_charge"]
        conecter = "-"  
        item_ids = [i for i, title in enumerate(titles) if title in use_items]
        x = conecter.join([item[i] for i in item_ids])
        return hashlib.md5(x.encode()).hexdigest()


    titles = [
            "Project1", "Project2", "Task", "Ticket", "Detail", "Is_Task",
            "Ready_date", "Due_date", "Estimation", "Update_Estimation",
            "In_charge",
            "Prev_task", "Next_task",
            "Status",
            "Begin_date_reg", "End_date_reg", "Man_hour_reg",
            "File_path", "Comment",
            "Priority",
            ]

    status = ["ToDo", "Doing", "Checking", "Done", "Pending"]
    members = ["できる社員", "すごい社員", "がんばる上司"]

    items = []
    items.append(["test", "case1", "task", "A", "", False, "", "", 5, 0, "がんばる上司", "", "", status[0], "", "", 0, "", "", 0, "#222222"])
    items.append(["test", "case1", "task", "B", "", False, "", "", 5, 0, "がんばる上司", "", "", status[0], "", "", 0, "", "", 8, "#222222"])
    items.append(["test", "case1", "task", "C", "", False, "", "2022/2/3", 3, 0, "がんばる上司", "", "", status[0], "", "", 0, "", "", 2, "#222222"])
    items.append(["test", "case1", "task", "D", "", False, "", "", 4, 0, "がんばる上司", "", "", status[0], "", "", 0, "", "", 3, "#222222"])
    items.append(["test", "case1", "task", "E", "", False, "", "", 3, 0, "がんばる上司", "", "", status[0], "", "", 0, "", "", 4, "#222222"])
    items.append(["test", "case1", "task", "F", "", False, "2022/2/4", "", 4, 0, "がんばる上司", "", "", status[0], "", "", 0, "", "", 5, "#222222"])
    items.append(["test", "case1", "task", "G", "", False, "", "2022/2/8", 2, 0, "がんばる上司", "", "", status[0], "", "", 0, "", "", 6, "#222222"])
    items.append(["test", "case1", "task2", "H", "", False, "", "", 15, 0, "がんばる上司", "", "", status[0], "", "", 0, "", "", 7, "#222222"])
    items.append(["test", "case2", "task", "I", "", False, "", "", 2, 0, "がんばる上司", "", "", status[0], "", "", 0, "", "", 1, "#222222"])

    indices = [str_to_hash_id(item, titles) for item in items]
    task_df = pd.DataFrame(items, columns=titles, index=indices)
    task_df["Update_Estimation"] = task_df["Estimation"]

    ticket = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
    prevt = ["","A", "B", "C", "C,F", "", "D,E", "", ""]
    nextt = ["B", "C", "D,E", "G", "G", "E", "", "", ""] 

    k2id = {}
    for t in ticket:
        tid = task_df[task_df["Ticket"] == t].index.item()
        k2id[t] = tid

    for t, p ,n in zip(ticket, prevt, nextt):
        task_df.loc[k2id[t], "Prev_task"] = ",".join([k2id[i] for i in p.split(",") if i])
        task_df.loc[k2id[t], "Next_task"] = ",".join([k2id[i] for i in n.split(",") if i])

    print(task_df.loc[:,["Ticket","Prev_task"]])
    print(task_df.loc[:,["Ticket","Next_task"]])
    # print(task_df)


    # %% =======================================================================
    # test use
    #===========================================================================
    hours_in_date = 6

    st = SortTickets(task_df, hours_in_date)
    st.calc_priority()

    print("number of tickets", st.num_tickets)
    print("due_time")
    print("ticket", "begin_limit", "ready_hour")
    for tid in st.tids:
        print(f"{st._ticket_id_to_ticket_name(tid)},{st.begin_limit[tid]:5d}, {st.ready_hour[tid]:5d}, {st.due_hour[tid]:5d}, {st.ready_date[tid]}, {st.due_date[tid]}")
    print("scheduling")
    for tid in st.sorted_tid:
        print(f"{st._ticket_id_to_ticket_name(tid)},{st.tid_pos[tid]}")


# %%
