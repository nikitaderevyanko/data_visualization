#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import re

from datetime import datetime


date_pattern = '%Y-%m-%d %X'


class ProcessInstance(object):
    def __init__(self, pid, start):
        self.pid = pid
        self.name = None
        self.start = start
        self.finish = start
        self.functions = dict()

    def __repr__(self):
        return 'Pid: {}\nFunctions: {}\n{}\t-\t{}\n'.format(
            self.pid,
            self.functions,
            self.start,
            self.finish
        )

    def add_func(self, names, logtime):
        self.name = names[0]
        for name in names:
            if name in self.functions:
                self.functions[name].update_time(logtime)
            else:
                self.functions[name] = ProcessName(name, logtime)
        self.finish = logtime


class ProcessName(object):
    def __init__(self, name, start):
        self.name = name
        self.start = start
        self.finish = start

    def __repr__(self):
        return '\n{}\t-\t{}\n'.format(
            self.start,
            self.finish
        )

    def __str__(self):
        return '\n{}\t-\t{}\n'.format(
            self.start,
            self.finish
        )

    def update_time(self, logtime):
        self.finish = logtime


class LogFileParser(object):
    def __init__(self, log_path):
        self.log_path = log_path
        self.process_info = dict()
        self.matcher = re.compile('\d*:')
        self.start = None
        self.finish = None
        self.timing = dict()
        self.total_time = None

    def __filter_by_delta(self, delta_pids, delta_funcs):
        pids_to_delete = []
        for pid, info in self.process_info.items():
            delta = info.finish - info.start
            if delta.total_seconds() < delta_pids:
                pids_to_delete.append(pid)
                continue
            funcs_to_delete = []
            for name, func in info.functions.items():
                delta = func.finish - func.start
                if delta.total_seconds() < delta_funcs:
                    funcs_to_delete.append(name)
            for name in funcs_to_delete:
                del info.functions[name]
        for pid in pids_to_delete:
            del self.process_info[pid]

    def __parse_functions(self, items, dt_object):
        names = []
        pid = None
        for item in items:
            match = self.matcher.match(item)
            if not match:
                names.append(item)
            else:
                pid = item[:-1]
                if pid not in self.process_info:
                    pi = ProcessInstance(pid, dt_object)
                    pi.add_func(names, dt_object)
                    self.process_info[pid] = pi
                else:
                    self.process_info[pid].add_func(names, dt_object)
                break

    def parse_log(self):
        with open(self.log_path, 'r') as f:
            for line in f.xreadlines():
                splitted = line.split()
                date_str = ' '.join(splitted[:2])
                date_str = date_str[:date_str.rfind(',')]
                dt_object = None
                try:
                    dt_object = datetime.strptime(
                        date_str,
                        date_pattern
                    )
                except ValueError:
                    continue
                if not self.start:
                    self.start = dt_object
                self.finish = dt_object
                self.__parse_functions(splitted[3:], dt_object)
            self.__filter_by_delta(5, 2)

    def total_time_period(self):
        delta = self.finish - self.start
        self.total_time = delta.total_seconds()

    def total_times_for_pids(self):
        for pid, pid_info in self.process_info.items():
            delta = pid_info.finish - pid_info.start
            total_time = delta.total_seconds()
            self.timing[pid] = total_time

    def filter_only_viewable(self, tolerance_sec=1000):
        self.viewable_timing = dict()
        for pid, total_time in self.timing.items():
            if total_time >= tolerance_sec:
                self.viewable_timing[pid] = total_time
