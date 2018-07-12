#!/usr/bin/env python3
import sys
import re
import os
import datetime

# Returns a list of filtered lines from the specified subtitle
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
                    s = re.sub(r'[^a-zA-Z,.?! \'-]', u'', s)
                    s = re.sub(r'- ', u'', s)
                    s = re.sub(r' -', u'', s)
                    if len(s) > 0 and s[0] == '-':
                        s = s[1:]
                    full_s = full_s + " " + s.strip()
                full_s = full_s.strip()
                if len(full_s) > 3:
                    # print("processing: ", full_s)
                    filtered.append(full_s)
                dialogue = []
            else:
                l = l.replace('<i>', '')
                l = l.replace('</i>', '')
                l = l.replace('\n', '')
                l = l.replace('\r', '')
                l = l.strip()
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
        training_data.append("===")

    new_filename = dir_name.replace('/', '') + ".txt"
    with open(new_filename, 'w+') as f:
        for l in training_data:
            f.write("%s\n" % l)

if __name__== "__main__":
    main()
