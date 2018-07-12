#!/usr/bin/env python3
import sys
import re
import os
import datetime

round = re.compile('\(.+?\)')
html = re.compile('\<.+?\>')
curly = re.compile('\{.+?\}')
square = re.compile('\[.+?\]')

def clean_string(s):
    s = re.sub(r'[^a-zA-Z,.?! \'-]', u'', s)
    s = re.sub(r'- ', u'', s)
    s = re.sub(r' -', u'', s)
    if len(s) > 0 and (s[0] == '-' or s[0] == '.'):
        s = s[1:]
    return s

# Returns a list of filtered lines from the specified subtitle
def get_filtered_data(filename):
    print("Filtering ", filename, "\r\n")
    filtered = []
    with open(filename, 'r') as f:
        space = True
        lines = f.readlines()
        dialogue = []
        if lines[0][0] == '{':
            space = False

        for l in lines:
            if l.strip().isdigit():
                continue
            if space and ("-->" in l or len(re.findall(r"(?:(?:([01]?\d|2[0-3]):)?([0-5]?\d):)?([0-5]?\d)", l)) > 0):
                continue
            if space and l.isspace():
                # process all
                full_s = ""
                for s in dialogue:
                    s = clean_string(s)
                    full_s = full_s + " " + s.strip()
                full_s = full_s.strip()
                if len(full_s.split(' ')) > 1:
                    # print("processing: ", full_s)
                    filtered.append(full_s)
                dialogue = []
            else:
                l = round.sub('', l)
                l = curly.sub('', l)
                l = square.sub('', l)
                l = html.sub('', l)
                l = l.replace('|', ' ')
                l = l.replace('. . .', '.')
                l = l.replace('\n', '')
                l = l.replace('\r', '')
                l = l.strip()
                # print(l)
                dialogue.append(l)

        if not space:
            for s in dialogue:
                s = clean_string(s)
                if len(s.split(' ')) > 1:
                    # print("processing: ", s)
                    filtered.append(s)

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
