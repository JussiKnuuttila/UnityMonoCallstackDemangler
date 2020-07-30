import argparse
import tkinter
import os
import re
import bisect
import win32file

parser = argparse.ArgumentParser(description="Demangle Unity Mono callstacks")
parser.add_argument("-p", "--pmip", metavar="PMIP_PATH")
parser.add_argument("-c", "--callstack", metavar="CALLSTACK_PATH")
args = parser.parse_args()

def temp_path():
    # TODO: Non-windows?
    return os.environ['TEMP']

def find_pmip_paths():
    pmip_pattern = re.compile(r"pmip_(\d+)_.*\.txt")
    temp_dir = temp_path()

    return [ temp_dir + '/' + f
        for f in os.listdir(temp_dir)
        if pmip_pattern.match(f) ]

# The pmip file is created with FILE_FLAG_DELETE_ON_CLOSE, which means
# we must open it with FILE_SHARE_DELETE.
def read_with_share_delete(filepath):
    h = win32file.CreateFile(filepath,
                             win32file.GENERIC_READ,
                             win32file.FILE_SHARE_READ |
                             win32file.FILE_SHARE_WRITE |
                             win32file.FILE_SHARE_DELETE,
                             None,
                             win32file.OPEN_EXISTING,
                             0,
                             0)

    if h != win32file.INVALID_HANDLE_VALUE:
        try:
            size = win32file.GetFileSize(h)
            hr, contents = win32file.ReadFile(h, size, None)
            if hr != 0:
                raise Exception("Failed to ReadFile")
            return contents.decode('utf-8').splitlines()
        except:
            win32file.CloseHandle(h)
    else:
        raise Exception("Failed to CreateFile")

def read_pmip_file(pmip_paths):
    for p in pmip_paths:
        try:
            return read_with_share_delete(p)
        except:
            pass

    return None

pmip_entry = re.compile(r"^\s*([0-9A-Fa-f]+)\s*;\s*([0-9A-Fa-f]+)\s*;\s*(.*)")

def parse_pmip_entry(pmip_line):
    m = pmip_entry.match(pmip_line)
    if m:
        return (int(m.group(1), base=16), int(m.group(2), base=16), m.group(3))
    else:
        return None

pmip_file_paths = None
callstack_lines = None
callstack_from_clipboard = False

if args.pmip:
    pmip_file_paths = [ args.pmip ]
else:
    pmip_file_paths = find_pmip_paths()

if args.callstack:
    with open(args.callstack, 'r') as f:
        callstack_lines = f.readlines()
else:
    try:
        callstack_lines = tkinter.Tk().clipboard_get().splitlines()
        callstack_from_clipboard = True
    except:
        callstack_lines = []

pmip_entries = [ parse_pmip_entry(line) for line in read_pmip_file(pmip_file_paths) ]
pmip_entries = [ e for e in pmip_entries if e ]
pmip_entries.sort()
pmip_begin_addresses = [ pmip[0] for pmip in pmip_entries ]

unknown_callstack_entry = re.compile(r"((>|\s)*)([0-9A-Fa-f]+)\(\)")

output = []

for l in callstack_lines:
    m = unknown_callstack_entry.match(l)
    if m:
        indent = m.group(1)
        address_text = m.group(3)
        address = int(address_text, base=16)
        index = bisect.bisect_right(pmip_begin_addresses, address) - 1
        if index >= 0 and index < len(pmip_entries):
            entry = pmip_entries[index]
            begin, end, symbol = entry
            assert begin == pmip_begin_addresses[index]
            if address >= begin and address < end:
                output.append("{0}{1}(): {2}".format(indent, address_text, symbol))
                continue

    output.append(l)

if callstack_from_clipboard:
    print("""CALLSTACK FROM CLIPBOARD
--------
""")

for l in output:
    print(l)

