#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import collections
import csv
import json
import sys


class Path:
    path: str = None
    pathlist: list = None
    isarray: bool = None
    isarraypath: bool = None
    multiplevalues: bool = None
    existing: int = None

    def __init__(self, path: str, pathlist: list, isarraypath: bool = None, existing: int = 1):
        self.path = path
        self.pathlist = pathlist
        self.isarraypath = isarraypath
        self.existing = existing

    def is_array(self) -> bool:
        if self.isarray is None:
            return False
        return self.isarray

    def is_arraypath(self) -> bool:
        if self.isarraypath is None:
            return False
        return self.isarraypath

    def has_multiple_values(self) -> bool:
        if self.multiplevalues is None:
            return False
        return self.multiplevalues


TWO_POINTS_PATH_PREFIX = ".."
TAB_PREFIX = "    "
ROOT_KEY = "."
ARRAY_VALUE = "ARRAY_VALUE_PLACEHOLDER"
JSON_TYPE_SWITCHER = {
    "<class 'dict'>": "{}",
    "<class 'list'>": "[]",
    "<class 'int'>": "(Integer)",
    "<class 'str'>": "(String)",
    "<class 'float'>": "(Decimal)",
    "<class 'bool'>": "(Boolean)",
    "<class 'NoneType'>": "(no object type)"
}
PATH_NUMBER = 'path_number'
FIELD_PATH = 'field_path'
MUTLIPLEVALUES = 'multiple_values'
EXISTING = 'existing'
HEADER = [PATH_NUMBER,
          FIELD_PATH,
          MUTLIPLEVALUES,
          EXISTING]


def generate_simple_path(fieldtuplelist):
    path_list = []
    for key, object_type in fieldtuplelist:
        if ARRAY_VALUE != key:
            path_list.append(key)
    path = '.'.join(path_list)
    if path.startswith(TWO_POINTS_PATH_PREFIX):
        return path[1:]
    return path


def generate_path_w_type(fieldtuplelist):
    path_list = []
    for key, object_type in fieldtuplelist:
        jsontype = JSON_TYPE_SWITCHER.get(object_type)
        if ARRAY_VALUE != key:
            path_list.append("\"" + key + "\" " + jsontype)
        else:
            last_path = path_list.pop()
            path_list.append(last_path + " " + jsontype)
    return ' > '.join(path_list)


def update_traverse_map(pathmap, pathlist, fromarray):
    path = generate_path_w_type(pathlist)
    if path not in pathmap:
        if fromarray:
            pathobject = Path(path, pathlist, True)
        else:
            pathobject = Path(path, pathlist)
        pathmap[path] = pathobject
    else:
        pathmap[path].existing += 1
    return pathmap


def update_travers_map_w_dict(existingpathmap, additionalpathmap):
    for path, pathlist in additionalpathmap.items():
        if path not in existingpathmap:
            existingpathmap[path] = pathlist
        else:
            existingpathmap[path].existing += 1
    return existingpathmap


def traverse(jsonnode, seedpathlist, key, fromarray):
    pathmap = {}
    currentpathlist = seedpathlist.copy()
    fieldtuple = (str(key), str(type(jsonnode)))
    currentpathlist.append(fieldtuple)
    pathmap = update_traverse_map(pathmap, currentpathlist, fromarray)
    # object/JSON node is JSON object
    if isinstance(jsonnode, dict):
        for objectkey, objectvalue in jsonnode.items():
            nexttraverse = traverse(objectvalue, currentpathlist, objectkey, False)
            pathmap = update_travers_map_w_dict(pathmap, nexttraverse)
    # object/JSON node is JSON array
    elif isinstance(jsonnode, list):
        path = generate_path_w_type(currentpathlist)
        pathobject = pathmap[path]
        pathobject.isarray = True
        # array has multiple values, i.e. field has multiple values
        if len(jsonnode) > 1:
            pathobject.multiplevalues = True
        pathmap[path] = pathobject
        for arrayelement in jsonnode:
            nexttraverse = traverse(arrayelement, currentpathlist, ARRAY_VALUE, True)
            pathmap = update_travers_map_w_dict(pathmap, nexttraverse)
    return pathmap


def csv_print(fieldstructurestatistics):
    with sys.stdout as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=HEADER, dialect='unix')

        writer.writeheader()
        for fieldstructurestatistic in fieldstructurestatistics:
            writer.writerow(fieldstructurestatistic)


def run():
    parser = argparse.ArgumentParser(prog='ldjstructurestats',
                                     description='Returns a structure statistics from given line-delimited JSON records. Eats line-delimited JSON records from stdin. Puts structure statistics calculated from the given line-delimited JSON records as pure CSV to stdout.',
                                     epilog='example: ldjstructurestats < [INPUT LINE-DELIMITED JSON RECORDS] > [PATH TO THE OUTPUT CSV FILE]',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    args = parser.parse_args()

    if hasattr(args, 'help') and args.help:
        parser.print_usage(sys.stderr)
        exit(-1)

    resultmap = {}
    for line in sys.stdin:
        jsonline = json.loads(line)
        seed = []
        traverseresult = traverse(jsonline, seed, ROOT_KEY, False)
        for path, pathobject in traverseresult.items():
            simple_path = generate_simple_path(pathobject.pathlist)
            if simple_path not in resultmap:
                pathmap = {path: pathobject}
                resultmap[simple_path] = pathmap
            else:
                resultpathobjects = resultmap[simple_path]
                if path not in resultpathobjects:
                    resultpathobjects[path] = pathobject
                else:
                    resultpathobject = resultpathobjects[path]
                    resultpathobject.existing += pathobject.existing
                    if pathobject.multiplevalues is True:
                        resultpathobject.multiplevalues = True
                    resultpathobjects[path] = resultpathobject

    # sort paths via OrderedDict
    orderedresultmap = collections.OrderedDict(sorted(resultmap.items()))

    fieldstructurestatistics = []
    path_number = 0
    for simplepath, pathobjects in orderedresultmap.items():
        overallexisting = 0
        path_number += 1
        for path, pathobject in pathobjects.items():
            if not pathobject.is_arraypath():
                overallexisting += pathobject.existing
        simplefieldstructurestatistic = {PATH_NUMBER: path_number,
                                         FIELD_PATH: simplepath,
                                         MUTLIPLEVALUES: None,
                                         EXISTING: overallexisting}
        fieldstructurestatistics.append(simplefieldstructurestatistic)
        for path, pathobject in pathobjects.items():
            hasmultiplevalues = None
            if pathobject.is_array():
                hasmultiplevalues = pathobject.has_multiple_values()
            path_prefix = TAB_PREFIX
            if pathobject.is_arraypath():
                path_prefix = path_prefix + path_prefix
            path_perfix_tab = "%s↳ " % path_prefix
            fieldstructurestatistic = {PATH_NUMBER: None,
                                       FIELD_PATH: path_perfix_tab + pathobject.path,
                                       MUTLIPLEVALUES: hasmultiplevalues,
                                       EXISTING: pathobject.existing}
            fieldstructurestatistics.append(fieldstructurestatistic)

    csv_print(fieldstructurestatistics)


if __name__ == "__main__":
    run()
