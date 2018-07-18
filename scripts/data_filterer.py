#!/usr/bin/env python3
import sys
import re
import os
import datetime
import argparse
import collections

class DataFilterer:
    round = re.compile('\(.+?\)')
    html = re.compile('\<.+?\>')
    curly = re.compile('\{.+?\}')
    square = re.compile('\[.+?\]')
    speaker = re.compile('^(.+?:|.+?>>)')

    availableDatatypes = collections.OrderedDict([  # OrderedDict because the first element is the default choice
        ('subs', "filterSubs"),
        ('transcript', "filterTranscript"),
    ])

    @staticmethod
    def dataTypeChoices():
        return list(DataFilterer.availableDatatypes.keys())

    @staticmethod
    def getFileContent(filename):
        lines = None
        with open(filename, 'r') as f:
            lines = f.readlines()
        return lines

    def __init__(self, args):
        self.dataType = args.dataType
        self.keepPunc = args.keepPunctuations
        self.filterMethod = DataFilterer.availableDatatypes[self.dataType]

    def _cleanLine(self, s):
        s = DataFilterer.round.sub('', s)
        s = DataFilterer.curly.sub('', s)
        s = DataFilterer.square.sub('', s)
        s = DataFilterer.html.sub('', s)
        s = s.strip()
        s = s.replace('|', ' ')
        s = s.replace('. . .', '.')
        s = s.replace('\n', '')
        s = s.replace('\r', '')
        if self.keepPunc:
            s = re.sub(r'[^a-zA-Z,.!? \'-]', u'', s)
        else:
            s = re.sub(r'[^a-zA-Z \'-]', u'', s)
        s = re.sub(r'- ', u'', s)
        s = re.sub(r' -', u'', s)
        if len(s) > 0 and (s[0] == '-' or s[0] == '.'):
            s = s[1:]
        return s.strip()

    def filterSubs(self, lines):
        filtered = []

        inlineTiming = None

        '''
        Two ways that subtitles are formatted:
        1. inlineTiming
            {330}{363} some sentence

        2. not inlineTiming
            1
            00:00:02,292 --> 00:00:03,645  X1:197 X2:518 Y1:484 Y2:524
            some sentence
        '''
        if lines[0][0] == '{':
            inlineTiming = True
        else:
            inlineTiming = False

        dialogue = [] # temporary array for a sentence that is written over multiple lines
        for l in lines:
            if l.strip().isdigit():
                continue
            if not inlineTiming and ("-->" in l or len(re.findall(r"(?:(?:([01]?\d|2[0-3]):)?([0-5]?\d):)?([0-5]?\d)", l)) > 0): # garbage lines
                continue
            if not inlineTiming and l.isspace(): # form one sentence using multiple lines of sentences
                full_s = ""
                for s in dialogue:
                    # Merge fragmented sub sentences into one sentence
                    s = self._cleanLine(s)
                    full_s = full_s + " " + s
                full_s = full_s.strip()
                if len(full_s) > 0:
                    filtered.append(full_s)
                dialogue = []
            else: # A line of sentence
                l = l.strip()
                if inlineTiming or (not inlineTiming and len(l) > 0 and l[0] == '-'):
                    # If begins with -, separate person speaking
                    l = self._cleanLine(l)
                    if len(l) > 0:
                        filtered.append(l)
                elif not inlineTiming:
                    # It could be one sentence written over multiple lines
                    dialogue.append(l)

        for s in dialogue:
            s = self._cleanLine(s)
            if len(s) > 0:
                filtered.append(s)

        return filtered

    def filterTranscript(self, lines):
        filtered = []
        for l in lines:
            if l.strip().isdigit(): # if just consists of digits, skip
                continue
            l = l.strip()

            l = DataFilterer.speaker.sub('', l)
            l = self._cleanLine(l)
            if len(l) > 0:
                filtered.append(l)

        return filtered

    # Returns a list of filtered lines from the specified subtitle
    def filterData(self, filename):
        print("Filtering ", filename, "\r\n")
        filtered = []

        filter = None
        try:
            filter = getattr(self, self.filterMethod)
        except AttributeError:
            raise NotImplementedError("Class `{}` does not implement `{}`".format(my_cls.__class__.__name__, method_name))

        lines = DataFilterer.getFileContent(filename)
        filtered = filter(lines)
        return filtered

def main(argv=None):
    if len(argv) < 2:
        return

    parser = argparse.ArgumentParser(description='Filter txt data.')
    parser.add_argument('--dataType', choices=DataFilterer.dataTypeChoices(), default=DataFilterer.dataTypeChoices()[0], help='type of txt files.')
    parser.add_argument('--dirName', type=str, default='', help='use this for directory name that contains the text files')
    parser.add_argument('mergeFiles', metavar='mf', type=str, nargs='*', help='Files to be added')
    parser.add_argument('--keepPunctuations', action='store_true', help='use this if you want train using a different dataset type')
    parser.add_argument('--mergeMode', action='store_true', help='use this if you want merge text files instead of filtering them')
    parser.add_argument('--outputName', type=str, default=None, nargs='?', help='use this if you want to specify output file name')

    # Parse arguments
    args = parser.parse_args(argv[1:])
    print(args)

    training_data = []
    new_filename = ""

    dataFilterer = DataFilterer(args)
    # Merge mode
    if args.mergeMode:
        for file in args.mergeFiles:
            new_filename += file.split(".")[0] + "_"
            training_data.extend(DataFilterer.getFileContent(file))
        new_filename = new_filename[:-1] + ".txt"
    # Filter mode
    else:
        # Get names of all text files to filter
        filenames = []
        for file in os.listdir(args.dirName):
            if file.endswith(".txt"):
                f = os.path.join(args.dirName, file)
                filenames.append(f)

        # Filter each file
        for filename in filenames:
            training_data.extend(dataFilterer.filterData(filename))
            training_data.append("===")

        new_filename = args.dirName.replace('/', '') + ".txt"

    if args.outputName is not None:
        new_filename = args.outputName

    with open(new_filename, 'w+') as f:
        for l in training_data:
            f.write("%s\n" % l)

if __name__== "__main__":
    main(sys.argv)
