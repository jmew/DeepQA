#!/usr/bin/env python3
import sys
import re
import os
import datetime

round = re.compile('\(.+?\)')
html = re.compile('\<.+?\>')
curly = re.compile('\{.+?\}')
square = re.compile('\[.+?\]')

speaker = re.compile('^.+?: ')

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
def get_filtered_data(filename, data_type):
    print("Filtering ", filename, "\r\n")
    final = []
    with open(filename, 'r') as f:

        '''
        Two ways that subtitles are formatted:
        1. subs_inline
            {330}{363} some sentence

        2. not subs_inline
            1
            00:00:02,292 --> 00:00:03,645  X1:197 X2:518 Y1:484 Y2:524
            some sentence
        '''
        subs_inline = None

        lines = f.readlines()
        dialogue = []

        if data_type == "subs":
            if lines[0][0] == '{':
                subs_inline = True
            else:
                subs_inline = False

        for l in lines:
            if l.strip().isdigit():
                continue
            if data_type == "subs" and not subs_inline and ("-->" in l or len(re.findall(r"(?:(?:([01]?\d|2[0-3]):)?([0-5]?\d):)?([0-5]?\d)", l)) > 0): # garbage lines
                continue
            if data_type == "subs" and not subs_inline and l.isspace(): # form one sentence using multiple lines of sentences
                full_s = ""
                for s in dialogue:
                    # Merge fragmented sub sentences into one sentence
                    s = clean_string(s)
                    full_s = full_s + " " + s
                full_s = full_s.strip()
                if len(full_s) > 0:
                    # print("processing: ", full_s)
                    final.append(full_s)
                dialogue = []
            else:
                l = l.strip()
                if data_type == "subs":
                    if subs_inline or (not subs_inline and len(l) > 0 and l[0] == '-'):
                        # If begins with -, separate person speaking
                        l = clean_string(l)
                        if len(l) > 0:
                            final.append(l)
                    elif not subs_inline:
                        # It could be one sentence written over multiple lines
                        dialogue.append(l)
                elif data_type == "transcript":
                    l = speaker.sub('', l)
                    l = clean_string(l)
                    if len(l) > 0:
                        final.append(l)

        if data_type == "subs":
            for s in dialogue:
                s = clean_string(s)
                if len(s) > 0:
                    # print("processing: ", s)
                    final.append(s)

    return final

def main():
    if len(sys.argv) != 3:
        print("python data_filterer.py <dir_name> <data_type: subs | transcript >")
        return

    dir_name = sys.argv[1]

    data_type = sys.argv[2]

    filenames = []
    for file in os.listdir(dir_name):
        if file.endswith(".txt"):
            f = os.path.join(dir_name, file)
            filenames.append(f)

    training_data = []
    for filename in filenames:
        training_data.extend(get_filtered_data(filename, data_type))
        training_data.append("===")

    new_filename = dir_name.replace('/', '') + ".txt"
    with open(new_filename, 'w+') as f:
        for l in training_data:
            f.write("%s\n" % l)

if __name__== "__main__":
    main()
