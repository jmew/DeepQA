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
    s = round.sub('', s)
    s = curly.sub('', s)
    s = square.sub('', s)
    s = html.sub('', s)
    s = s.strip()
    s = s.replace('|', ' ')
    s = s.replace('. . .', '.')
    s = s.replace('\n', '')
    s = s.replace('\r', '')
    s = re.sub(r'[^a-zA-Z,.?! \'-]', u'', s)
    s = re.sub(r'- ', u'', s)
    s = re.sub(r' -', u'', s)
    if len(s) > 0 and (s[0] == '-' or s[0] == '.'):
        s = s[1:]
    return s.strip()

# Returns a list of filtered lines from the specified subtitle
def get_filtered_data(filename):
    print("Filtering ", filename, "\r\n")
    filtered = []
    with open(filename, 'r') as f:

        '''
        Two ways that subtitles are formatted:
        1. inline
            {330}{363} some sentence

        2. not inline
            1
            00:00:02,292 --> 00:00:03,645  X1:197 X2:518 Y1:484 Y2:524
            some sentence
        '''
        inline = False

        lines = f.readlines()
        dialogue = []
        if lines[0][0] == '{':
            inline = True

        for l in lines:
            if l.strip().isdigit():
                continue
            if not inline and ("-->" in l or len(re.findall(r"(?:(?:([01]?\d|2[0-3]):)?([0-5]?\d):)?([0-5]?\d)", l)) > 0):
                continue
            if not inline and l.isspace():
                full_s = ""
                for s in dialogue:
                    # Merge fragmented sub sentences into one sentence
                    s = clean_string(s)
                    full_s = full_s + " " + s
                full_s = full_s.strip()
                if len(full_s) > 0:
                    # print("processing: ", full_s)
                    filtered.append(full_s)
                dialogue = []
            else:
                l = l.strip()
                if len(l) > 0 and l[0] == '-':
                    # If begins with -, separate person speaking
                    l = clean_string(l)
                    filtered.append(l)
                else:
                    # It could be one sentence written over multiple lines
                    dialogue.append(l)

        if inline:
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
