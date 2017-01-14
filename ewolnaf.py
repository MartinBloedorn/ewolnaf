#!/usr/bin/python

"""
ewol - Eclipse Workaround for Linked Resources

Manage linked resources - e.g. source files, linker scripts, ASM-files - for Eclipse.

Use Makefile-like variables and declarions on an arbitrary list file, e.g. src.list:

    # Comments and nested variables are supported
    SDK_ROOT := D:/Arquivos/Projetos/3rdparty/coldvision/software/nrf52_workspace/nRF5_SDK
    COMP_DIR := $(SDK_ROOT)/components

    # Entries must be grouped in folders, such as root '/', ...
    /: # this is the root
    $(COMP_DIR)/libraries/button/app_button.c
    $(COMP_DIR)/libraries/util/app_error.c
    $(COMP_DIR)/libraries/fifo/app_fifo.c
    $(COMP_DIR)/libraries/timer/app_timer.c

    # And 'src/ble' subfolder. 
    src/ble/: 
    $(SDK_ROOT)/components/ble/common/ble_advdata.c # another comments (just keep a space between the text and the `#`)
    $(SDK_ROOT)/components/ble/ble_advertising/ble_advertising.c
    $(SDK_ROOT)/components/ble/common/ble_conn_params.c
    $(SDK_ROOT)/components/ble/ble_services/ble_nus/ble_nus.c
    $(SDK_ROOT)/components/ble/common/ble_srv_common.c

Then push your modifications to Eclipse:
    $ ./ewolnaf.py /path/to/project/ /path/of/src.list --push

Or create a new src.list by pulling linked data from your project:
    $ ./ewolnaf.py /path/to/project/ /path/of/src.list --pull
"""

import sys, os, argparse, re
import xml.etree.ElementTree as ET
from argparse import RawTextHelpFormatter


def parseProjectFile(projdir):
    """
    Reads the .project file in projdir and returns a dictionary containing:
    - Group key
        - Tuple list (name, location)
    """
    prjlist = {}    

    tree = ET.parse(projdir + '/.project')
    root = tree.getroot()
    
    for lr in root.iter('linkedResources'):
        for link in root.iter('link'):
            m = re.match('(?P<folder>\/?.*\/)?(?P<name>.*)', link.find('name').text)
            if m is not None and m.group('folder') and m.group('name'):
                if m.group('folder') not in prjlist:
                    prjlist[m.group('folder')] = []
                prjlist[m.group('folder')].append((m.group('name'), link.find('location').text))
            else:
                print('Unrecognized <name>: {}'.format(link.find('name').text))
    print(prjlist)    
    return prjlist


def writeProjectFile(projdir, prjlist):
    """
    Great documentation.
    """
    tree = ET.parse(projdir + '/.project')    
    root = tree.getroot()
    # Write backup
    tree.write(projdir + '/.project.backup')

    # Remove existing resources, add fresh tag
    for lr in root.iter('linkedResources'):
        root.remove(lr)        
    lr = ET.SubElement(root, 'linkedResources')
    for _fldr in prjlist:
        for _tuple in prjlist[_fldr]:
            link = ET.SubElement(lr, 'link')
            ET.SubElement(link, 'name').text = _fldr + _tuple[0]
            ET.SubElement(link, 'type').text = '1'
            ET.SubElement(link, 'location').text = _tuple[1]
    tree.write(projdir + '/.project')    


def parseSourceList(srcfile):
    """
    Does stuff.
    """
    lineno   = 0
    currfldr = '/'
    
    srclist  = {}
    varlist  = {}         
    
    srcfd = open(srcfile, 'r')
    if srcfd.closed:
        print('Could not open {}'.format(srcfile))
        sys.exit()

    for line in srcfd:
        lineno = lineno + 1
        # Is a comment
        if re.match('[\s\t]*#.*', line) is not None:
            continue        
        # Is a variable
        m = re.match('[\s\t]*(?P<varname>\S*)[\s\t]*:=[\s\t]*(?P<varcontent>\S*)[\s\t]*(#.*)?', line)
        if m is not None and m.group('varname') and m.group('varcontent'):
            varlist[m.group('varname')] = m.group('varcontent')
            continue
        # If it's not a comment nor variable, try to expand variables on line:
        line = expandVariables(line, varlist)
        # Is a group (name followed by ':' and at last one space, e.g., 'app/: ')
        m = re.match('[\s\t]*(?P<folder>\$?\S*):[\s\t]+', line)
        if m is not None and m.group('folder'):
            currfldr = m.group('folder').strip()
            if currfldr not in srclist:
                srclist[currfldr] = []
            continue
        # Is an entry
        m = re.match('[\s\t]*(?P<entry>.*((\/)|(\\\\))(?P<name>\S*))#?', line)
        if m is not None:
            if currfldr not in srclist:
                print('Something wrong with the source list. Check your groups (perhaps you forgot the \'/:\'?)\nAborting.')
                sys.exit()
            srclist[currfldr].append((m.group('name').strip(), m.group(1).strip()))
    #print(srclist)
    #print(varlist)
    srcfd.close()
    return srclist


def writeSourceList(srcfile, srclist):
    srcfd = open(srcfile, 'w+')
    if srcfd.closed:
        print('Could not write at {}'.format(srcfile))
        sys.exit()
    for _fldr in srclist:
        srcfd.writelines('{}:\n'.format(_fldr))
        for _tuple in srclist[_fldr]:
            srcfd.writelines('{}\n'.format(_tuple[1]))
        srcfd.writelines('\n')    
    srcfd.close()


def expandVariables(line, varlist):
    m = []
    while m is not None:
        #print('Expanding = {}'.format(line))
        m = re.match('(.*)\$\((?P<varname>\w*)\)(.*)', line)
        if m is not None:
            if m.group('varname') not in varlist:
                print('Undefined variable {}'.format(m.group('varname')))
                sys.exit()
            line = m.group(1) + varlist[m.group('varname')] + m.group(3)
    return line


def printSourceList(srclist):
    print('\nSOURCES:\n')
    for _fldr in srclist:
        print('{}:'.format(_fldr))
        for _tuple in srclist[_fldr]:
            print('   {} =\n   \t{}'.format(_tuple[0], _tuple[1]))
        print('\n')
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Eclipse Workaround for Linked Resources\n\n"
                                     "Quickly add/remove lots of linked resources to/from an Eclipse project.\n"
                                     "Usage:\n./ewol.py /path/to/project /path/to/list/file.txt --push|--pull",
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('projdir',   help='Project directory')
    parser.add_argument('srcfile',   help='Source list file')
    parser.add_argument('--push',    help='Overwrites project\'s linked resources with the list\'s contents. Creates backup.', action='store_true')
    parser.add_argument('--pull',    help='Stores the project\'s linked resources in the list file.', action='store_true')
    
    args = parser.parse_args()    

    if args.pull and args.push:
        print('Make up your mind: push or pull?')
        sys.exit()

    # `input` backwards compatibility
    if sys.version_info[0] >= 3:
        get_input = input
    else:
        get_input = raw_input

    if args.pull:
        # Read project and build index
        prjlist = parseProjectFile(args.projdir)
        printSourceList(prjlist)
        ans = get_input('Save list to file {}? [y/N] '.format(args.srcfile))
        if ans.strip() == 'y':
            print('Saving...')
            writeSourceList(args.srcfile, prjlist)
        else:
            print('Aborted.')

    elif args.push:
        # Read source list and build index
        srclist = parseSourceList(args.srcfile)
        printSourceList(srclist)
        ans = get_input('Push to .project file in {}? (.project.backup will be created) [y/N] '.format(args.projdir))
        if ans.strip() == 'y':
            print('Pushing...')
            writeProjectFile(args.projdir, srclist)
        else:
            print('Aborted.')

    else:
        print('Choose an operation: --pull or --push')
    
