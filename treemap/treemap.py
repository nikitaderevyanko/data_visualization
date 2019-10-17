#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import pandas as pd
import aggdraw

from enum import Enum
from PIL import Image


MainParameter = Enum('width', 'height')
MAX_COLOR_VALUE = 255
CATEGORIES_DATA_SHEET_ID = 0


def init_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--width',
        metavar='w',
        type=int,
        help='Width of picture',
        default=300,
    )
    parser.add_argument(
        '--height',
        metavar='h',
        type=int,
        help='Height of picture',
        default=300,
    )
    parser.add_argument(
        '--data-path',
        metavar='d',
        type=str,
        help='Path to input data file',
        required=True,
    )
    parser.add_argument(
        '--output-path',
        metavar='o',
        type=str,
        help='Path to output file',
        required=True,
    )

    return parser.parse_args()


class Rectangle(object):
    def __init__(self, params, main_param):
        self.width = params[0]
        self.height = params[1]
        self.main_param = main_param

    def __str__(self):
        return "{}x{}".format(self.width, self.height)

    def __repr__(self):
        return "{}x{}".format(self.width, self.height)


class TreeMap(object):
    def __init__(self, data_path, image_path, width, height):
        self.__data_path = data_path
        self.__image_path = image_path
        self.__width = width
        self.__height = height
        self._parse_xls()

        self.objects = []
        self.image = Image.new(
            "RGBA",
            (self.__width, self.__height),  # size
            (MAX_COLOR_VALUE, MAX_COLOR_VALUE, MAX_COLOR_VALUE, MAX_COLOR_VALUE)  # white background
        )

    @staticmethod
    def count_aspect_ratio(volume, main_size_param):
        secondary_size_param = volume / main_size_param
        return float(main_size_param) / secondary_size_param

    @staticmethod
    def deduce_main_param(params):
        width, height = params
        if width <= height:
            return MainParameter.width
        return MainParameter.height

    @staticmethod
    def deduce_rectangles_sizes(volumes, width, height):
        def update_results():
            for item in processed:
                item_main_param = int(item / secondary_param)
                sizes = [0, 0]
                sizes[main_param.index] = item_main_param
                sizes[(main_param.index + 1) % 2] = int(secondary_param)
                results.append(Rectangle(sizes, main_param))

        aspect_ratio = None
        cur_volume = 0
        params = [width, height]
        main_param = TreeMap.deduce_main_param(params)
        processed = []
        results = []
        for volume in volumes:
            cur_aspect_ratio = TreeMap.count_aspect_ratio(volume, params[main_param.index])
            if aspect_ratio is None:
                aspect_ratio = cur_aspect_ratio
                cur_volume += volume
                processed.append(volume)
            elif aspect_ratio > cur_aspect_ratio:
                aspect_ratio = cur_aspect_ratio
                cur_volume += volume
                processed.append(volume)
            else:
                secondary_param = float(cur_volume) / params[main_param.index]
                update_results()

                processed = [volume]
                cur_volume = volume
                secondary_index = (main_param.index + 1) % 2
                params[secondary_index] = params[secondary_index] - int(secondary_param)
                main_param = TreeMap.deduce_main_param(params)
                aspect_ratio = TreeMap.count_aspect_ratio(volume, params[main_param.index])

        secondary_param = float(cur_volume) / params[main_param.index]
        update_results()
        return results

    def draw_picture(self):
        res = TreeMap.deduce_rectangles_sizes(self.__categories_volumes, self.__width, self.__height)
        length = len(res)
        iterable = zip(res, self.__data.keys(), range(length))
        draw = aggdraw.Draw(self.image)
        begin = [0, 0]
        for r, k, i in iterable:
            last_begin = begin[:]
            categories_data = self.__data[k]
            total_volume = categories_data.sum()
            coefficient = float(r.width * r.height) / total_volume
            categories_volumes = [
                int(coefficient * volume)
                for volume in categories_data.values
            ]
            q = TreeMap.deduce_rectangles_sizes(categories_volumes, r.width, r.height)
            delta = MAX_COLOR_VALUE / len(q)
            start = [0, 0, 0]
            start[i] += delta
            for j, a in enumerate(q):
                if j + 1 == len(q):
                    end = [last_begin[0] + r.height, last_begin[1] + r.width]
                else:
                    end = [begin[0] + a.height, begin[1] + a.width]
                draw.rectangle(
                    begin + end,
                    aggdraw.Pen(tuple(start), 0.5),
                    aggdraw.Brush(tuple(start))
                )
                start[i] += delta
                if str(a.main_param) == "width":
                    begin[0] += a.height
                else:
                    begin[1] += a.width
            if str(r.main_param) == "width":
                begin = [last_begin[0] + r.height, last_begin[1]]
            else:
                begin = [last_begin[0], last_begin[1] + r.width]
        draw.flush()
        self.image.save(self.__image_path, "PNG")

    def _parse_xls(self):
        xls = pd.ExcelFile(self.__data_path)
        sheet = xls.parse(CATEGORIES_DATA_SHEET_ID)  # 0 is the sheet number
        sub_categories = sheet['Sub-Category']
        categories_data = sheet['Category'].value_counts()
        self.__data = {}
        for category in categories_data.keys():
            categ_relations = sub_categories[sheet['Category'] == category].value_counts()
            self.__data[category] = categ_relations
        total_volume = categories_data.sum()
        self.__coefficient = float(self.__width * self.__height) / total_volume
        self.__categories_volumes = [
            int(self.__coefficient * volume)
            for volume in categories_data.values
        ]


def main(args):
    treeMap = TreeMap(
        data_path=args.data_path,
        image_path=args.output_path,
        width=args.width,
        height=args.height
    )
    treeMap.draw_picture()


if __name__ == '__main__':
    args = init_args()
    main(args)
