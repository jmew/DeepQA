#!/usr/bin/env python3
import sys
import re
import os
import datetime
 
def get_filtered_data(filename):
    print("Filtering ", filename, "\r\n")
    filtered = []
    with open(filename, 'r') as f:
        lines = f.readlines()
        dialogue = []
        for l in lines:
            if l.strip().isdigit():
                continue
            if "-->" in l or '[' in l or '(' in l:
                continue
            if l.isspace():
                # process all
                full_s = ""
                for s in dialogue:
                    full_s = full_s + " " + s.strip()
                # full_s = re.search('[a-zA-z](.+?)', full_s).group(0)
                full_s = re.sub(r'[^a-zA-Z,.?! \'-]', u'', full_s)
                full_s = re.sub(r'- ', u'', full_s)
                full_s = re.sub(r' -', u'', full_s)
                # full_s = re.sub(r'([^\s\w]|_)+', '', full_s)
                full_s = full_s.strip()
                if len(full_s) > 3: 
                    # if full_s[0] == "-":
                    #      full_s = full_s[1:]
                
                    # print "processing: ", full_s
                    filtered.append(full_s)
                dialogue = []
            else:
                l = l.replace('<i>', '')
                l = l.replace('</i>', '')
                l = l.replace('\n', '')
                l = l.replace('\r', '')
                l = l.strip()
                # if len(l) > 0 and l[0] == '-':
                #    l = l[1:]
                #if "Thrilling" in l:
                #    print l
                # print l
                dialogue.append(l)
    
    return filtered 

def main():
    if len(sys.argv) != 2:
        print("Enter in the directory name")
        return

    dir_name = sys.argv[1]

    filenames = []
    for file in os.listdir(dir_name):
        if file.endswith(".txt"):
            f = os.path.join(dir_name, file) 
            filenames.append(f)
   
    training_data = [] 
    for filename in filenames:
        training_data.extend(get_filtered_data(filename))

    new_filename = dir_name.replace('/', '') + ".txt"
    with open(new_filename, 'w+') as f:
        for l in training_data:
            f.write("%s\n" % l)

if __name__== "__main__":
    main()

