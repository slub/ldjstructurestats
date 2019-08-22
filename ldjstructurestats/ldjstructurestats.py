#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import collections
import csv
import json
import sys


class Path:
    path = None
    pathlist = None
    isarray = None
    isarraypath = None
    multiplevalues = None
    pathoccurrence = None

    def __init__(self, path, pathlist, isarraypath=None, pathoccurrence=1):
        self.path = path
        self.pathlist = pathlist
        self.isarraypath = isarraypath
        self.pathoccurrence = pathoccurrence

    def is_array(self):
        if self.isarray is None:
            return False
        return self.isarray

    def is_arraypath(self):
        if self.isarraypath is None:
            return False
        return self.isarraypath

    def has_multiple_values(self):
        if self.multiplevalues is None:
            return False
        return self.multiplevalues


class ResultPath:
    pathmap = None
    existing = None
    multiple_path_occurences_by_record = None

    def __init__(self, pathmap, existing=1):
        self.pathmap = pathmap
        self.existing = existing

    def has_multiple_path_occurences_by_record(self):
        return self.multiple_path_occurences_by_record


TWO_POINTS_PATH_PREFIX = ".."
TAB_PREFIX = "    "
ROOT_KEY = "."
ARRAY_VALUE = "ARRAY_VALUE_PLACEHOLDER"
JSON_OBJECT_TYPE = "<class 'dict'>"
JSON_ARRAY_TYPE = "<class 'list'>"
NO_OBJECT_TYPE = "<class 'NoneType'>"
BOOLEAN_TYPE = "<class 'bool'>"
DECIMAL_TYPE = "<class 'float'>"
STRING_TYPE = "<class 'str'>"
INTEGER_TYPE = "<class 'int'>"
JSON_TYPE_SWITCHER = {
    JSON_OBJECT_TYPE: "{}",
    JSON_ARRAY_TYPE: "[]",
    INTEGER_TYPE: "(Integer)",
    STRING_TYPE: "(String)",
    DECIMAL_TYPE: "(Decimal)",
    BOOLEAN_TYPE: "(Boolean)",
    NO_OBJECT_TYPE: "(no object type)"
}
PATH_NUMBER = 'path_number'
FIELD_PATH = 'field_path'
MULTIPLEPATHS = 'multiple_paths'
MUTLIPLEVALUES = 'multiple_values'
PATH_EXISTING = 'path_existing'
PATH_OCCURRENCE = 'path_occurrence'
HEADER = [PATH_NUMBER,
          FIELD_PATH,
          MULTIPLEPATHS,
          MUTLIPLEVALUES,
          PATH_EXISTING,
          PATH_OCCURRENCE]


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
        pathmap[path].pathoccurrence += 1
    return pathmap


def update_travers_map_w_dict(existingpathmap, additionalpathmap):
    for path, pathlist in additionalpathmap.items():
        if path not in existingpathmap:
            existingpathmap[path] = pathlist
        else:
            existingpathmap[path].pathoccurrence += 1
    return existingpathmap


def traverse(jsonnode, seedpathlist, key, fromarray):
    pathmap = collections.OrderedDict()
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
        recordpathlist = []
        for path, pathobject in traverseresult.items():
            simple_path = generate_simple_path(pathobject.pathlist)
            recordpathadded = False
            if not pathobject.is_arraypath() and simple_path not in recordpathlist:
                recordpathlist.append(simple_path)
                recordpathadded = True

            if simple_path not in resultmap:
                pathmap = collections.OrderedDict()
                pathmap[path] = pathobject
                resultmap[simple_path] = ResultPath(pathmap)
            else:
                resultpath = resultmap[simple_path]
                if recordpathadded:
                    # count path existence by record
                    resultpath.existing += 1
                resultpathobjects = resultpath.pathmap
                if path not in resultpathobjects:
                    resultpathobjects[path] = pathobject
                else:
                    resultpathobject = resultpathobjects[path]
                    resultpathobject.pathoccurrence += pathobject.pathoccurrence
                    if pathobject.multiplevalues is True:
                        resultpathobject.multiplevalues = True
                    resultpathobjects[path] = resultpathobject
                resultmap[simple_path] = resultpath

    # sort paths via OrderedDict
    orderedresultmap = collections.OrderedDict(sorted(resultmap.items()))

    fieldstructurestatistics = []
    path_number = 0
    for simplepath, resultpath in orderedresultmap.items():
        overallpathoccurrence = 0
        path_number += 1
        pathobjects = resultpath.pathmap
        for path, pathobject in pathobjects.items():
            if not pathobject.is_arraypath():
                overallpathoccurrence += pathobject.pathoccurrence
        multiplepaths = None
        if resultpath.existing < overallpathoccurrence:
            multiplepaths = True
        simplefieldstructurestatistic = {PATH_NUMBER: path_number,
                                         FIELD_PATH: simplepath,
                                         MULTIPLEPATHS: multiplepaths,
                                         MUTLIPLEVALUES: None,
                                         PATH_EXISTING: resultpath.existing,
                                         PATH_OCCURRENCE: overallpathoccurrence}
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
                                       MULTIPLEPATHS: None,
                                       MUTLIPLEVALUES: hasmultiplevalues,
                                       PATH_EXISTING: None,
                                       PATH_OCCURRENCE: pathobject.pathoccurrence}
            fieldstructurestatistics.append(fieldstructurestatistic)

    csv_print(fieldstructurestatistics)


if __name__ == "__main__":
    run()
