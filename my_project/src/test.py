import os
import sys
import re
import subprocess


#executable_file = input("What is the name of the executable file?\n")
executable_file = "myprogram_test"
if not os.path.isfile(executable_file):
    raise Exception("The executable file you just typed does not exists")


# load source file    
def load_source (file_name):
    if os.path.isfile(file_name):
        source = open(file_name, "r")   
        
        # dictionary = {line_number, []}
        dictionary = {} 
        
        # iteration through all lines
        line_number = 1
        for line in source.readlines(): 
            
            dictionary[str(line_number)] = [str(line_number)+": "+line.strip("\n"), "not_stmt", "not_occured"]
        
            #print("At line {}, content: {}".format(line_number, line.strip("\n")) )
            line_number += 1
        
        source.close()
        return dictionary
    
    else:
        raise Exception("The source file, {}, does not exist",file_name)
        

  



#--------------------- llvm-dwarfdump --------------------------
# load llvm-dwarfdump command output to .txt
dwarfdump_file = open("dwarfdump.txt", mode='w')
subprocess.run(["llvm-dwarfdump","--debug-line",executable_file], stdout= dwarfdump_file)
dwarfdump_file.close()

# get names of associated source file and capture the correct table
dwarfdump_file = open("dwarfdump.txt", mode='r')

# --------------------- source file ------------------------------

# load source file into dictionary
#dictionary of source (source_dict) = {"file_name": {"line_number": ["souce code", "not_stmt/is_stmt", "occured/not_occured"],}, }
source_dict = {}


# First, capture below
'''
"standard_opcode_lengths[DW_LNS_set_isa] = 1
file_names[  1]:
           name: "test.rs""
'''

previous_line = ""
current_line = dwarfdump_file.readline()

pattern_file_name = re.compile(r'file_names\[\s*(\d*)\]:')
pattern_previous_line = re.compile(r'include_directories')
pattern_name = re.compile(r'\s+name: "(.+)"\n')
pattern_begin_address = re.compile(r'0x0*([a-z0-9]+)\s+(\d+)\s+\d+\s+\d+\s+\d+\s+\d+\s+([a-zA-Z_]*)(\s[a-zA-Z_]*)*\n')

captured = False


array_file_names = []


#dictionary of address table = {file_name: {address: [line ,flags([])] , } , ... ], }
dict_dwarf = {}

#capture the "file_names[  1]:", "name: "xxxx.rs"" and table
while ((current_line != "")):
    match_obj = pattern_file_name.match(current_line)
    
    #match "file_names[  1]:"
    if (match_obj and (match_obj[1] == "1")):
        # check previous line
        if not (pattern_previous_line.match(previous_line)):
            captured = True

        else:
            captured = False
    
    #if captured, load file_name and try to match table
    if (captured):
        match_name = pattern_name.match(current_line)

        if match_name:
            #store file name
            array_file_names.append(match_name[1]) 
            source_dict[match_name[1]] = load_source(match_name[1])
            dict_dwarf[match_name[1]] = {} 
        
        match_address = pattern_begin_address.match(current_line)
        
        if (match_address):
            if match_address[3] == "is_stmt":
                dict_dwarf[array_file_names[-1]][match_address[1]] = [match_address[2], match_address[3]]
                source_dict[array_file_names[-1]][match_address[2]][1] = "is_stmt"
            else:
                dict_dwarf[array_file_names[-1]][match_address[1]] = [match_address[2], ""]
            
            #print(match_address[1])
        #else:
        #    print("{} is not matched", current_line[:20])
            
    previous_line = current_line
    current_line = dwarfdump_file.readline()

dwarfdump_file.close()

# file_begin_end = {filename: {"begin": "address", "end"="address"} , ...}
file_begin_end = {}
for file_name, assemblys in dict_dwarf.items():
    file_begin_end[file_name] = {}
    file_begin_end[file_name]["begin"] = list(assemblys)[0]
    file_begin_end[file_name]["end"] = list(assemblys)[-1]
    
print(file_begin_end) 


file_source = open("source_test.txt", "w")
print(source_dict, file = file_source) 
file_source.close()

file_dwarf = open ("dwarf_test.txt", "w")
print(dict_dwarf, file = file_dwarf)
file_dwarf.close()
              
                
       
    






#-------------------------- objdump -----------------------
# load objdump_file
objdump_file = open("objdump.txt", mode='w')
subprocess.run(["objdump","-d",executable_file], stdout= objdump_file)
objdump_file.close()


#dictionary of assembly table = {filename: {address: byte code and assembly, } , }
dict_objdump = {}

for file_name in list(dict_dwarf):
    dict_objdump[file_name] = {}

pattern_address_assembly = re.compile(r'\s+([a-z0-9]+):\s+([a-z0-9]{2}\s)+.*')
with open("objdump.txt", mode='r') as objdump_file:
    line = objdump_file.readline()
    
    
    while line:
        
        match_obj = pattern_address_assembly.match(line)

        if (match_obj):
            
            for file_name, address in file_begin_end.items():
                if file_begin_end[file_name]["begin"] <= match_obj[1] <=  file_begin_end[file_name]["end"]:
                    dict_objdump[file_name][match_obj[1]] = match_obj.group()
                

        line = objdump_file.readline()
        
#print(dict_objdump)    
file_objdump = open ("objdump_test.txt", "w")
print(dict_objdump, file = file_objdump)
file_objdump.close()





html_file = open("table.html", "w")

html_file.write("""<!DOCTYPE html>
<html lang=\"en\">

<head>
    <meta charset=\"utf-8\">
    <title>CSC 254 A4</title>
    <style type=\"text/css\">
        body {font-size: 17px}

        table { 
            width: 100%; 
            border-radius: solid 1px; 
            border-collapse: collapse;
        }    

        th {width: 50%}

        td { 
            padding: 4px;
            vertical-align: top; }
    </style>
</head>

<body>""")

#dictionary of source (source_dict) = {"file_name": {"line_number": ["souce code", "not_stmt/is_stmt", "occured/not_occured"],}, }

#dictionary of address table (dict_dwarf) = {file_name: {"address": "line" ,flags("is_stmt" or ""), } , ... ] }

#dictionary of assembly table (dict_objdump)= {file_name: {"address": "address, byte code and assembly", } , }

# HTML [source] - [[address-byte-assembly], ... ]- 

for file_name, address_assembly_dic  in dict_objdump.items():
    

    html_file.write("""
    <table border=\"1\">
        <tr>
            <th colspan=\"2\">"""+file_name+"""</th>
        </tr>
        <tr>
            <th>Assembly</th>
            <th>Source</th>
        </tr>""")
    
    index = 0
    
   
    address_assemblys = list(address_assembly_dic.items())
    #print(address_assemblys)
    length_items = len(address_assemblys)
    print(length_items)
    
        
    while index < length_items:
        #if dict_dwarf[file_name][address][1] == "is_stmt" :
            #address, address_assembly = address_assemblys[index]
            
        html_file.write("""
        <tr>
            <td>""")
        
        html_file.write("""
            <div>"""+address_assemblys[index][1]+"""</div>""")
        

        reach_next_statement = False
            
        while ((index < (length_items-1)) and (not reach_next_statement)) :
            
            if  address_assemblys[index+1][0] in dict_dwarf[file_name]:
                #print("First if statement: "+str(index+1) +" " +address_assemblys[index+1][0])
                if (dict_dwarf[file_name][address_assemblys[index+1][0]][1] == "") : 
                    html_file.write("""
                    <div>"""+address_assemblys[index+1][1]+"""</div>""")
                    index += 1
                else:
                    reach_next_statement = True
            else:
                #print("First else statement: "+ str(index+1) +" " +address_assemblys[index+1][0])
                html_file.write("""
                <div>"""+address_assemblys[index+1][1]+"""</div>""")
                index += 1
                        
        html_file.write("""
            </td>""")
        
        html_file.write("""
            <td>"""+"""
                <div>source<div>"""+"""
            </td>""")
            
        html_file.write("""
        </tr>
        """)
        
        index += 1
           
'''  
  <tr>
    <td>January</td>
    <td>$100</td>
  </tr>
  <tr>
    <td>February</td>
    <td>
        <div>$50</div>
        <div>$50</div>
    </td>

  </tr>
'''
html_file.write("\n</table>")

    