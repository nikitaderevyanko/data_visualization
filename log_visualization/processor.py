#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import argparse

from parser import LogFileParser
from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)
from colour import Color


def init_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--width',
        type=int,
        help='Width of picture',
        default=1000,
    )
    parser.add_argument(
        '--height',
        type=int,
        help='Height of picture',
        default=1000,
    )
    parser.add_argument(
        '--log-file',
        type=str,
        help='Path to input data file',
        required=True,
    )
    parser.add_argument(
        '--output-path',
        type=str,
        help='Path to output file',
        required=True,
    )

    return parser.parse_args()


class PrintableProcess(object):
    def __init__(
            self,
            start,
            length,
            height,
            pid_width,
            num,
            color,
            info
    ):
        self.x_start = start
        self.length = length
        self.height = height
        self.pid_width = int(pid_width)
        self.num = num
        self.color = color
        self.info = info
        self.x_finish = self.x_start + self.length
        self.y_start = (self.num - 1) * self.height
        self.y_finish = self.num * self.height

    def get_coordinates(self):
        start_coord = (
            int(self.pid_width + self.x_start),
            int(self.y_start)
        )
        finish_coords = (
            int(self.pid_width + self.x_finish),
            int(self.y_finish)
        )
        return start_coord, finish_coords, self.color

    def get_pid_coordinates(self):
        y_coord = (self.y_start + self.y_finish) / 2.
        start_coord = (int(self.pid_width / 5.), int(y_coord))
        return start_coord, self.info.pid

    def get_name_coordinates(self):
        name = "function %d" % self.num
        font = ImageFont.load_default()
        text_x, text_y = font.getsize(name)
        y_coord = (self.y_start + self.y_finish) / 2.
        y_coord -= text_y / 2.
        x_coord = (self.x_start + self.x_finish) / 2.
        x_coord = x_coord + self.pid_width - text_x / 2.
        start_coord = (int(x_coord), int(y_coord))
        return start_coord, name


class PrintableProcesses(object):
    def __init__(self, width=2000, height=1000):
        self.total_width = float(width)
        self.pid_width = min(100.0, self.total_width / 10.)
        self.right_margin = self.pid_width
        self.width = self.total_width - self.pid_width - self.right_margin
        self.height = float(height)

    def __convert_colors(self, rgb):
        return tuple(map(lambda x: int(x * 255), rgb))

    def scale_bars(self, lfp):
        self.print_list = list()
        self.bars_count = len(lfp.viewable_timing)
        self.bar_height = float(self.height) / self.bars_count
        self.colors = list(
            Color("blue").range_to(Color("red"), self.bars_count)
        )
        self.colors = map(
            lambda x: self.__convert_colors(x.rgb),
            self.colors
        )
        counter = 1
        for pid, total_time in lfp.viewable_timing.items():
            pid_info = lfp.process_info[pid]
            start_delta = (pid_info.start - lfp.start).total_seconds()
            start_len = start_delta * self.width / lfp.total_time
            proc_len = total_time * self.width / lfp.total_time
            self.print_list.append(
                PrintableProcess(
                    start=start_len,
                    length=proc_len,
                    height=self.bar_height,
                    pid_width=self.pid_width,
                    num=counter,
                    color=self.colors[counter - 1],
                    info=pid_info
                )
            )
            counter += 1


def print_bars(pps, output):
    result_img = Image.new(
        'RGBA',
        (int(pps.total_width), int(pps.height)),
        "white"
    )
    draw = ImageDraw.Draw(result_img)
    for pp in pps.print_list:
        start, finish, color = pp.get_coordinates()
        draw.rectangle((start, finish), fill=color)
        start_pid, pid = pp.get_pid_coordinates()
        text = "PID %s" % pid
        draw.text(start_pid, text, "black")
        start_name, name = pp.get_name_coordinates()
        draw.text(start_name, name, "black")

    result_img.save(output, "PNG")


def main():
    args = init_args()
    lfp = LogFileParser(args.log_file)
    lfp.parse_log()
    lfp.total_time_period()
    lfp.total_times_for_pids()
    lfp.filter_only_viewable()
    pps = PrintableProcesses()
    pps.scale_bars(lfp)
    print_bars(pps, args.output_path)

if __name__ == "__main__":
    main()
