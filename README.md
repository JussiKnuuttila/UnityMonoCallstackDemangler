# UnityMonoCallstackDemangler
Python script that resolves symbols for Unity Mono JIT callstacks. Requires pywin32.

Usage:
* Start unity with mixed callstack debugging enabled (creates `%TEMP%/pmip_<pid>_<id>.txt` that contains symbols)
* Copy a callstack from visual studio to clipboard
* Run `python UnityMonoCallstackDemangler.py` from command line
