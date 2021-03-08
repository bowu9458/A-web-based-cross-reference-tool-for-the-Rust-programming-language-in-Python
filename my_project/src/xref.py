import os
import sys
import re
import subprocess
from datetime import datetime

if not os.path.exists('XREF'):
    os.makedirs('XREF')
    

#executable_file = input("What is the name of the executable file?\n")
executable_file = "myprogram_test"
if not os.path.isfile(executable_file):
    raise Exception("The executable file you just typed does not exists")

def find_all(all_str, sub_str):
    index_list = []
    index = all_str.find(sub_str)
    sub_len = len(sub_str)
    while index != -1:
        index_list.append(index)
        index = all_str.find(sub_str, index + sub_len)

    
    return index_list
    
    
def highlight_comment(comment):
    # comment -> light grey
    comment_highlight = "<span style=\"color: Gray\">"+comment+"</span>"
    return comment_highlight
    
def highlight_string(string): 
    # string -> green
    string_highlight = " <span style=\"color: Green\">"+string+"</span> "
    return string_highlight


keyword_pattern = pattern_previous_line = re.compile(r'[^a-zA-Z0-9_-](?P<keyword>if|else if|else|false|true|fn|for|in|mod|use|return|while|break|do|let|mut|pub)[^a-zA-Z0-9_-]')  


  
def highlight_keyword(matched):
    # key_word -> red
    return "<span style=\"color: Red\">"+" "+matched.group('keyword')+" "+"</span>"
        

def sub_keyword(source):
    return re.sub(keyword_pattern, highlight_keyword, source)
    
    
def add_color (source):
    # simple syntax highlighter
    #check whether there is any comment (begin with "//")
    comment_begin = source.find("//")
    newstring = ""
    if comment_begin != -1:
        # there is comment
        #check whether this commnet is inside a string
        string_position = find_all(source,"\"")
        if len(string_position) == 0:
            # no string
            newstring = source[:comment_begin] + highlight_comment(source[comment_begin:])
        else:
            #print("there is string!: "+ source)
            #there is string, check whether it contains the comment
            begin = string_position[0]
            end = string_position[-1]
            if string_position[0] < comment_begin < string_position[-1]:
                #string contain comment
                newstring = sub_keyword(" "+source[:begin]) + highlight_string(source[begin:end+1]) + sub_keyword(" "+source[end+1:])
            elif comment_begin > string_position[0]:
                #string is in front of comment
                newstring = sub_keyword(" "+source[:begin]) + highlight_string(source[begin:end+1]) + source[end+1:comment_begin] + highlight_comment(source[comment_begin:])
            else:
                newstring = sub_keyword(" "+source[:comment_begin]) + highlight_comment(source[comment_begin:])
    else:
        #no comment, check string
        string_position = find_all(source,"\"")
        if len(string_position) == 0:
            newstring = sub_keyword(" "+source)
        else:
            begin = string_position[0]
            end = string_position[-1]
            newstring = source[:begin] 

            newstring  += highlight_string(source[begin:end+1]) 
            newstring += sub_keyword(" "+source[end+1:])
    
    
    
    return newstring

# load source file    
def load_source (file_name):
    if os.path.isfile(file_name):
        source = open(file_name, "r")   
        
        # dictionary = {line_number, []}
        dictionary = {} 
        
        # iteration through all lines
        line_number = 1
        for line in source.readlines(): 
            
            dictionary[str(line_number)] = [str(line_number)+": "+add_color(line), "not_stmt", "not_occured"]
        
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
pattern_previous_line_prefix = re.compile(r'include_directories\[\s*[0-9a-z+]\] = "(.+)"')
pattern_previous_line = re.compile(r'include_directories\[\s*[0-9a-z+]\] = "/')
pattern_name = re.compile(r'\s+name: "(.+)"\n')
pattern_begin_address = re.compile(r'0x0*([a-z0-9]+)\s+(\d+)\s+\d+\s+\d+\s+\d+\s+\d+\s+([a-zA-Z_]*)(\s[a-zA-Z_]*)*\n')

captured = False


array_file_names = []
name_prefix =""

#dictionary of address table = {file_name: {address: [line ,flags([])] , } , ... ], }
dict_dwarf = {}

#capture the "file_names[  1]:", "name: "xxxx.rs"" and table
while ((current_line != "")):
    match_obj = pattern_file_name.match(current_line)
    
    
    #match "file_names[  1]:"
    if (match_obj and (match_obj[1] == "1")):
        # check previous line
        
        if not (pattern_previous_line.match(previous_line)):
            #source are within sibling directory
            captured = True
            name_prefix = ""
            
            match_obj = pattern_previous_line_prefix.match(previous_line)
            if match_obj:
                name_prefix = match_obj[1]
            
        else:
            captured = False
    
    #if captured, load file_name and try to match table
    if (captured):
       
        match_name = pattern_name.match(current_line)
        if match_name:
            if name_prefix == "":    
                source_name = match_name[1]
            else:
                #print(name_prefix+"/"+match_name[1])
                source_name = name_prefix+"/"+match_name[1]
            
            #store file name
            array_file_names.append(source_name) 
            source_dict[source_name] = load_source(source_name)
            dict_dwarf[source_name] = {} 
        
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
    
#print(file_begin_end) 


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

pattern_address_assembly = re.compile(r'\s+([a-z0-9]+):\s+(([a-z0-9]{2}\s)+)\s*(.*)')
with open("objdump.txt", mode='r') as objdump_file:
    line = objdump_file.readline()

    
    while line:
        
        match_obj = pattern_address_assembly.match(line)

        if (match_obj):
            
            for file_name, address in file_begin_end.items():
                if file_begin_end[file_name]["begin"] <= match_obj[1] <=  file_begin_end[file_name]["end"]:
                    if match_obj.group(4):
                        dict_objdump[file_name][match_obj[1]] = "<a " + "id=\""+match_obj.group(1)+"\">"+match_obj.group(1)+":</a> "+ match_obj.group(2)+" "+ match_obj.group(4)
                        #print(match_obj.group(4))
                    else:
                        dict_objdump[file_name][match_obj[1]] = "<a " + "id=\""+match_obj.group(1)+"\">"+match_obj.group(1)+":</a> "+ match_obj.group(2)

        line = objdump_file.readline()
        
#print(dict_objdump)    
file_objdump = open ("objdump_test.txt", "w")
print(dict_objdump, file = file_objdump)
file_objdump.close()


html_home_file = open("XREF/home.html", "w")
html_home_file.write("""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="utf-8">
    <title>CSC 254 A4</title>
    <style type="text/css">
        body {font-size: 25px;
            text-align: center; 
            vertical-align: middle;}

        

    </style>
</head>

<body>""")


time = str(datetime.now())
path = os.path.realpath(__file__)

html_home_file.write("""
<div>Run Time:"""+ time+"""</div>
<div>Run Path:"""+ path+"""</div>
""")


html_home_file.write("""
<div><a href="main.html#main.rs" >Link to main in cross index</a>  </div>  
<div><a href="main.html" >Link to cross index</a></div>

</body>
</html>""")
html_home_file.close()



html_file = open("XREF/main.html", "w")

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
            vertical-align: top; 
            width: 50%
        }
        
        div{
            margin-top: 5px;
            margin-bottom: 5px;
            font-size: 14px;
        }

    </style>
</head>

<body>""")

#dictionary of source (source_dict) = {"file_name": {"line_number": ["souce code", "not_stmt/is_stmt", "occured/not_occured"],}, }

#dictionary of address table (dict_dwarf) = {file_name: {"address": "line" ,flags("is_stmt" or ""), } , ... ] }

#dictionary of assembly table (dict_objdump)= {file_name: {"address": "address, byte code and assembly", } , }

# HTML [source] - [[address-byte-assembly], ... ]- 



pattern_merge_top = re.compile(r'[0-9]+:((\s*}\s*\n)|(\s*\n))')

#------------------ organize/merge source code --------------------

previous_statement = 0

for file_name, line_source in source_dict.items():
    accumlate = ""
    for line_number, source_info in line_source.items():
        #print(line_number)
        if source_info[1] == "not_stmt" :
            
            if pattern_merge_top.match(source_info[0]) and previous_statement != 0:

                #merge top
                source_dict[file_name][str(previous_statement)][0] += "<br>"+source_info[0]
            else:
                #merge down
                accumlate += source_info[0]+"<br>"
            
        else:
            previous_statement = int(line_number)
            source_dict[file_name][line_number][0] = accumlate + source_dict[file_name][line_number][0]
            accumlate = ""

    previous_statement = 0


def linker(matched):
    address_linker = "<a href=\"#"+matched.group('address')+"\">"+ matched.group('address') +"</a>"
    return address_linker


def add_linker(source):
    new_source = re.sub('(jmp|jne|je|jg|callq)\s+(?P<address>[0-9a-z]+)', linker, source)
    return new_source


    
for file_name, address_assembly_dic  in dict_objdump.items():

    html_file.write("""
    <table border=\"1\">
        <tr>
            <th colspan=\"2\">"""+"<a " + "id=\""+file_name+"\">"+file_name+"</a>"+"""</th>
        </tr>
        <tr>
            <th>Assembly</th>
            <th>Source</th>
        </tr>""")
    
    index = 0
    
   
    address_assemblys = list(address_assembly_dic.items())

    length_items = len(address_assemblys)
    #print(length_items)
    
    previous_line = "0"   
    while index < length_items:
        source = ""
        if dict_dwarf[file_name][address_assemblys[index][0]][1] == "is_stmt" :
            line = dict_dwarf[file_name][address_assemblys[index][0]][0]
            
            if source_dict[file_name][line][2] == "not_occured":
                source = source_dict[file_name][line][0]
                source_dict[file_name][line][2] = "occured"
            else:
                source = "<div style=\"background-color: gray\">"+source_dict[file_name][line][0]+"</div>"
            
        html_file.write("""
        <tr>
            <td>""")
        
        html_file.write("""
            <div>"""+add_linker(address_assemblys[index][1])+"""</div>""")
        
        
        reach_next_statement = False
            
        while ((index < (length_items-1)) and (not reach_next_statement)) :
            if  address_assemblys[index+1][0] in dict_dwarf[file_name]:
                if (dict_dwarf[file_name][address_assemblys[index+1][0]][1] == "") : 
                    
                    html_file.write("""
                    <div>"""+add_linker(address_assemblys[index+1][1])+"""</div>""")
                    index += 1
                    
                else:
                    if previous_line == dict_dwarf[file_name][address_assemblys[index+1][0]][0]:
                        html_file.write("""
                        <div>"""+add_linker(address_assemblys[index+1][1])+"""</div>""")
                        index += 1

                    else:
                        previous_line = dict_dwarf[file_name][address_assemblys[index+1][0]][0]
                        reach_next_statement = True
            else:
                html_file.write("""
                <div>"""+add_linker(address_assemblys[index+1][1])+"""</div>""")
                index += 1
                        
        html_file.write("""
            </td>""")
        
        
        html_file.write("""
            <td>"""+"""
                <div>"""+source+"""</div>"""+"""
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

html_file.close()