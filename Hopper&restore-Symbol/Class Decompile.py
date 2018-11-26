# -*- coding: utf-8 -*-

import re
import gc
import os


IGNORED_CLASS_PREFIXES = [
    'AFNetwork', 'AFHTTP', 'AFURL', 'AFSecurity',
    'Flurry', 'FMDatabase',
    'MBProgressHUD', 'MJ',
    'SDWebImage',
]


IGNORED_CLASS_LABEL_NAMES = [
    '-[ClassName methodName:]',
]


def is_ignored_class(class_name):
    for prefix in IGNORED_CLASS_PREFIXES:
        if class_name.startswith(prefix):
            return True
    return False


def is_ignored_method(label_name):
    for name in IGNORED_CLASS_LABEL_NAMES:
        if name == label_name:
            return True
    return False


#pragma mark - Save File

def get_file_path(class_name):
    return '%s/%s.m'%(path, class_name)


def get_file_header(class_name):
    return '''\
//
//  %s.m
//
//  Generated by Class Decompile.
//  Repository is https://github.com/poboke/Class-Decompile
//  Copyright © 2016 www.poboke.com. All rights reserved.
//

@implementation %s

'''%(class_name, class_name)


def get_file_footer():
    return '''\
@end
'''


#pragma mark - Decompile

def parse_label_name(label_name):
    result = re.search(r'^([+-])\[(.+)\s(.+)\]', label_name)
    if result:
        symbol, class_name, method_name = result.groups()
        params_count = method_name.count(':')
        params = tuple(['arg%d'%(i+2) for i in range(params_count)])
        method_name = method_name.replace(':', ':(id)%s ')%(params)
        method_name = '%s (%%s)%s'%(symbol, method_name)
        return (class_name, method_name)
    else:
        return (None, None)


def start_decompile(input_class_name=None):
    classes = {}
    total_count = 0
    for i in range(segment.getProcedureCount()):
        procedure = segment.getProcedureAtIndex(i)
        address = procedure.getEntryPoint()

        label_name = segment.getNameAtAddress(address)
        if not label_name:
            continue
        if is_ignored_method(label_name):
            continue

        class_name, method_name = parse_label_name(label_name)
        if not class_name:
            continue
        if input_class_name and class_name != input_class_name:
            continue
        if is_ignored_class(class_name):
            continue
        if os.path.exists(get_file_path(class_name)):
            continue

        procedure.label_name = label_name
        procedure.method_name = method_name
        classes.setdefault(class_name, []).append(procedure)
        total_count += 1

    print 'total count :', total_count

    current_count = 0
    for class_name in classes:
        print '\n***** %s *****'%(class_name)
        codes = get_file_header(class_name)
        procedures = classes[class_name]
        for procedure in procedures:
            current_count += 1
            percent = (float(current_count) / total_count) * 100
            print '%05.2f%%  |  %s'%(percent, procedure.label_name)
            pseudo_code = procedure.decompile()
            if not pseudo_code:
                continue
            match = re.match(r'.+return\s.+;', pseudo_code, re.DOTALL)
            method_type = 'id' if match else 'void'
            method_name = procedure.method_name%method_type
            codes += '%s\n{\n%s}\n\n'%(method_name, pseudo_code)
        codes += get_file_footer()

        file_path = get_file_path(class_name)
        with open(file_path, 'w') as file:
            file.write(codes)

        del codes
        gc.collect()

    print 'Done!'


document = Document.getCurrentDocument()
segment = document.getSegmentByName('__TEXT')

app_name = document.getExecutableFilePath().split('/')[-1]
path = os.path.expanduser('~/ClassDecompiles/' + app_name)
if not os.path.exists(path):
    os.makedirs(path)

message = 'Please choose the decompile type:'
buttons = ['Decompile All Classes', 'Decompile One Class', 'Cancel']
button_index = document.message(message, buttons)
if button_index == 0:
    start_decompile()
elif button_index == 1:
    message = 'Please input the class name:'
    input_class_name = document.ask(message)
    if input_class_name is None:
        print 'Cancel decompile!'
    elif input_class_name == '':
        print 'Class name can not be empty!'
    else:
        start_decompile(input_class_name)
elif button_index == 2:
    print 'Cancel decompile!'
