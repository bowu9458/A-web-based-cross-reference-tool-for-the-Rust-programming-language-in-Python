import os
import sys
import re
import subprocess

'''
current_line = "wqe\n"
pattern = re.compile(r'\n')
match_obj = pattern.match(current_line)
if (match_obj):
    print("true") 
    
    if match_obj.group(1) == "1123":
        print("great")
    '''
'''    
current_line = "0x0000000000006590     18      6      1   0             0 t"
pattern_begin_address = re.compile(r'0x0*(\d+)\s+(\d+)\s+\d+\s+\d+\s+\d+\s+\d+\s+([a-zA-Z_])*')
match_address = pattern_begin_address.match(current_line)
if (match_address):
    print(match_address[3])
    if not match_address[3]:
        print ("empty flag")

current_line = "0x0000000000006590     18      6      1   0             0 t"
print(current_line[:20])
'''
'''
current_line = "    6281:    8b 44 24 0c \n"
pattern_begin_address = re.compile(r'\s+([a-z0-9]+):\s+([a-z0-9]{2}\s)+.*');
match_address = pattern_begin_address.match(current_line)
if (match_address):
    print(match_address[1])
    print(match_address.group()) 
'''





