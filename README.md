# ldjstructurestats - line-delimited JSON structure statistics

ldjstructurestats is a commandline command (Python3 program) that determines the structure of given line-delimited JSON records.

This tool can be utilised to discover the structure (+ schema) of given line-delimited JSON records and possible differences/variants at single field paths. Furthermore, it also illustrates, whether a certain field path can contain multiple values or not.

## Usage

It eats line-delimited JSON records from *stdin*.

It puts structure statistics calculated from the given line-delimited JSON records as pure CSV to *stdout*.

```
ldjstructurestats

optional arguments:
  -h, --help                           show this help message and exit
```

* example:
    ```
    ldjstructurestats < [INPUT LINE-DELIMITED JSON RECORDS] > [PATH TO THE OUTPUT CSV FILE]
    ```
## Run

* clone this git repo or just download the [ldjstructurestats.py](ldjstructurestats/ldjstructurestats.py) file
* run ./ldjstructurestats.py
* for a hackish way to use ldjstructurestats system-wide, copy to /usr/local/bin

### Install system-wide via pip

```
sudo -H pip3 install --upgrade [ABSOLUTE PATH TO YOUR LOCAL GIT REPOSITORY OF LDJSTRUCTURESTATS]
```
(which provides you ```ldjstructurestats``` as a system-wide commandline command)

## Description

#### Statistics Header

#### path_number

* a number/count for each (simple) path/field

#### field_path

* the field path
* rows that have a number in the column 'path_number', contain the simple field path
  * field names (/keys) in simple field paths are separated by a `.`  
* rows below a line with a simple field path, contain the structure variants/mutations of this simple field path
  * field names (/keys) in structure variant field paths are separated by ` > `
  * field names (/keys) in structure variant field paths are enclosed in quotation marks (`"`) 
  * indent = 1 tab + '↳' at the beginning of the field path
* rows below structure variants/mutations that end with a *JSON array*, contain the structure variant field paths incl. the object types that can occur in this *JSON array*
  * indent = 2 tabs + '↳' at the beginning of the field path

#### multiple_values

* **only** if, the field path (i.e. structure variant field path) ends with a *JSON array*, this column is either filled with `True` or `False`
   * `True` = this field path has *JSON arrays* with multiple values
   * `False` = this field path only has *JSON arrays* that do not contain multiple values, i.e., they are single-valued

#### existing

* the existing count of the simple field path or its structure variant in the line-delimited JSON records
* note: for leaf field paths this existing count is usually equal to its occurence count 

### Structure Field Path Notation

* behind each field name in a structure field path is a notation of the object type of the value of this field (/key)
* these object types include all possible JSON object types, which are

   |Object Type Notation|JSON Object Type|
   |--------------------|----------------|
   | {} | JSON object |
   | [] | JSON array |
   | (Integer) | integer number |
   | (String) | string value |
   | (Decimal) | decimal number |
   | (Boolean) | boolean value |
   | (no object type) | `null` value, i.e., no value |

* the notation of the *JSON array* object types is `[]` + `[ARRAY VALUE OBJECT TYPE]`, i.e. `[ARRAY VALUE OBJECT TYPE]` can be one of `{}`, `(Integer)`, `(String)`, `(Decimal)`, `(Boolean)` or `(no object type)`, e.g. `[] {}` or `[] (String)`
