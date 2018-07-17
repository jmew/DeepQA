# Copyright 2015 Conchylicultor. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""
Main script. See README.md for more information

Use python 3
"""

import argparse  # Command line parsing
import configparser  # Saving the models parameters
import datetime  # Chronometer
import os  # Files management
import tensorflow as tf
import numpy as np
import math

from tqdm import tqdm  # Progress bar
from tensorflow.python import debug as tf_debug

from chatbot.textdata import TextData
from chatbot.model import Model


class Chatbot:
    """
    Main class which launch the training or testing mode
    """

    class TestMode:
        """ Simple structure representing the different testing modes
        """
        ALL = 'all'
        INTERACTIVE = 'interactive'  # The user can write his own questions
        DAEMON = 'daemon'  # The chatbot runs on background and can regularly be called to predict something

    def __init__(self):
        """
        """
        # Model/dataset parameters
        self.args = None

        # Task specific object
        self.textData = None  # Dataset
        self.model = None  # Sequence to sequence model

        # Tensorflow utilities for convenience saving/logging
        self.writer = None
        self.saver = None
        self.modelDir = ''  # Where the model is saved
        self.globStep = 0  # Represent the number of iteration for the current model

        # TensorFlow main session (we keep track for the daemon)
        self.sess = None

        # Filename and directories constants
        self.MODEL_DIR_BASE = 'save' + os.sep + 'model'
        self.MODEL_NAME_BASE = 'model'
        self.MODEL_EXT = '.ckpt'
        self.CONFIG_FILENAME = 'params.ini'
        self.CONFIG_VERSION = '0.5'
        self.TEST_IN_NAME = 'data' + os.sep + 'test' + os.sep + 'samples.txt'
        self.TEST_OUT_SUFFIX = '_predictions.txt'
        self.SENTENCES_PREFIX = ['Q: ', 'A: ']

    @staticmethod
    def parseArgs(args):
        """
        Parse the arguments from the given command line
        Args:
            args (list<str>): List of arguments to parse. If None, the default sys.argv will be parsed
        """

        parser = argparse.ArgumentParser()

        # Global options
        globalArgs = parser.add_argument_group('Global options')
        globalArgs.add_argument('--test', action='store_true', default=True)
        globalArgs.add_argument('--createDataset', action='store_true',
                                help='if present, the program will only generate the dataset from the corpus (no training/testing)')
        globalArgs.add_argument('--playDataset', type=int, nargs='?', const=10, default=None,
                                help='if set, the program  will randomly play some samples(can be use conjointly with createDataset if this is the only action you want to perform)')
        globalArgs.add_argument('--reset', action='store_true', default=False,
                                help='use this if you want to ignore the previous model present on the model directory (Warning: the model will be destroyed with all the folder content)')
        globalArgs.add_argument('--verbose', action='store_true',
                                help='When testing, will plot the outputs at the same time they are computed')
        globalArgs.add_argument('--debug', action='store_true',
                                help='run DeepQA with Tensorflow debug mode. Read TF documentation for more details on this.')
        globalArgs.add_argument('--keepAll', action='store_true',
                                help='If this option is set, all saved model will be kept (Warning: make sure you have enough free disk space or increase saveEvery)')  # TODO: Add an option to delimit the max size
        globalArgs.add_argument('--modelTag', type=str, default=None,
                                help='tag to differentiate which model to store/load')
        globalArgs.add_argument('--rootDir', type=str, default="",
                                help='folder where to look for the models and data')
        globalArgs.add_argument('--watsonMode', action='store_true',
                                help='Inverse the questions and answer when training (the network try to guess the question)')
        globalArgs.add_argument('--autoEncode', action='store_true',
                                help='Randomly pick the question or the answer and use it both as input and output')
        globalArgs.add_argument('--device', type=str, default=None,
                                help='\'gpu\' or \'cpu\' (Warning: make sure you have enough free RAM), allow to choose on which hardware run the model')
        globalArgs.add_argument('--seed', type=int, default=None, help='random seed for replication')

        # Dataset options
        datasetArgs = parser.add_argument_group('Dataset options')
        datasetArgs.add_argument('--corpus', choices=TextData.corpusChoices(), default=TextData.corpusChoices()[0], help='corpus on which extract the dataset.')
        datasetArgs.add_argument('--datasetTag', type=str, default='', help='add a tag to the dataset (file where to load the vocabulary and the precomputed samples, not the original corpus). Useful to manage multiple versions. Also used to define the file used for the lightweight format.')  # The samples are computed from the corpus if it does not exist already. There are saved in \'data/samples/\'
        datasetArgs.add_argument('--ratioDataset', type=float, default=1.0, help='ratio of dataset used to avoid using the whole dataset')  # Not implemented, useless ?
        datasetArgs.add_argument('--maxLength', type=int, default=10, help='maximum length of the sentence (for input and output), define number of maximum step of the RNN')
        datasetArgs.add_argument('--filterVocab', type=int, default=1, help='remove rarelly used words (by default words used only once). 0 to keep all words.')
        datasetArgs.add_argument('--skipLines', action='store_true', help='Generate training samples by only using even conversation lines as questions (and odd lines as answer). Useful to train the network on a particular person.')
        datasetArgs.add_argument('--vocabularySize', type=int, default=40000, help='Limit the number of words in the vocabulary (0 for unlimited)')

        # Network options (Warning: if modifying something here, also make the change on save/loadParams() )
        nnArgs = parser.add_argument_group('Network options', 'architecture related option')
        nnArgs.add_argument('--hiddenSize', type=int, default=512, help='number of hidden units in each RNN cell')
        nnArgs.add_argument('--numLayers', type=int, default=2, help='number of rnn layers')
        nnArgs.add_argument('--softmaxSamples', type=int, default=0, help='Number of samples in the sampled softmax loss function. A value of 0 deactivates sampled softmax')
        nnArgs.add_argument('--initEmbeddings', action='store_true', help='if present, the program will initialize the embeddings with pre-trained word2vec vectors')
        nnArgs.add_argument('--embeddingSize', type=int, default=64, help='embedding size of the word representation')
        nnArgs.add_argument('--embeddingSource', type=str, default="GoogleNews-vectors-negative300.bin", help='embedding file to use for the word representation')

        # Training options
        trainingArgs = parser.add_argument_group('Training options')
        trainingArgs.add_argument('--numEpochs', type=int, default=30, help='maximum number of epochs to run')
        trainingArgs.add_argument('--saveEvery', type=int, default=2000, help='nb of mini-batch step before creating a model checkpoint')
        trainingArgs.add_argument('--batchSize', type=int, default=256, help='mini-batch size')
        trainingArgs.add_argument('--learningRate', type=float, default=0.002, help='Learning rate')
        trainingArgs.add_argument('--dropout', type=float, default=0.9, help='Dropout rate (keep probabilities)')

        return parser.parse_args(args)

    def run(self, args=None):
        """
        Launch the training and/or the interactive mode
        """
        print('Welcome to DeepQA v0.1 !')
        print()
        print('TensorFlow detected: v{}'.format(tf.__version__))

        self.args = self.parseArgs(args)

        if not self.args.rootDir:
            self.args.rootDir = os.getcwd()  # Use the current working directory

        self.loadModelParams()  # Update the self.modelDir and self.globStep, for now, not used when loading Model (but need to be called before _getSummaryName)
        self.textData = TextData(self.args)

        tf.reset_default_graph()
        # Prepare the model
        with tf.device(self.getDevice()):
            self.model = Model(self.args, self.textData)
        self.saver = tf.train.Saver(max_to_keep=200)

        # Running session
        self.sess = tf.Session(config=tf.ConfigProto(
            allow_soft_placement=True,  # Allows backup device for non GPU-available operations (when forcing GPU)
            log_device_placement=False)  # Too verbose ?
        )  # TODO: Replace all sess by self.sess (not necessary a good idea) ?

        self.sess.run(tf.global_variables_initializer())
        # Reload the model eventually (if it exist.), on testing mode, the models are not loaded here (but in predictTestset)
        self.managePreviousModel(self.sess)
        print("Done")

    def predict(self, inp):
        if inp == '' or inp == 'exit':
            return

        questionSeq = []  # Will be contain the question as seen by the encoder
        answer = self.singlePredict(inp, questionSeq)
        if not answer:
            return
        return self.textData.sequence2str(answer, clean=True)


    def singlePredict(self, question, questionSeq=None):
        """ Predict the sentence
        Args:
            question (str): the raw input sentence
            questionSeq (List<int>): output argument. If given will contain the input batch sequence
        Return:
            list <int>: the word ids corresponding to the answer
        """
        # Create the input batch
        batch = self.textData.sentence2enco(question)
        if not batch:
            return None
        if questionSeq is not None:  # If the caller want to have the real input
            questionSeq.extend(batch.encoderSeqs)

        # Run the model
        ops, feedDict = self.model.step(batch)
        output = self.sess.run(ops[0], feedDict)  # TODO: Summarize the output too (histogram, ...)
        answer = self.textData.deco2sentence(output)

        return answer


    def loadEmbedding(self, sess):
        """ Initialize embeddings with pre-trained word2vec vectors
        Will modify the embedding weights of the current loaded model
        Uses the GoogleNews pre-trained values (path hardcoded)
        """

        # Fetch embedding variables from model
        with tf.variable_scope("embedding_rnn_seq2seq/rnn/embedding_wrapper", reuse=True):
            em_in = tf.get_variable("embedding")
        with tf.variable_scope("embedding_rnn_seq2seq/embedding_rnn_decoder", reuse=True):
            em_out = tf.get_variable("embedding")

        # Disable training for embeddings
        variables = tf.get_collection_ref(tf.GraphKeys.TRAINABLE_VARIABLES)
        variables.remove(em_in)
        variables.remove(em_out)

        # If restoring a model, we can leave here
        if self.globStep != 0:
            return

        # New model, we load the pre-trained word2vec data and initialize embeddings
        embeddings_path = os.path.join(self.args.rootDir, 'data', 'embeddings', self.args.embeddingSource)
        embeddings_format = os.path.splitext(embeddings_path)[1][1:]
        print("Loading pre-trained word embeddings from %s " % embeddings_path)
        with open(embeddings_path, "rb") as f:
            header = f.readline()
            vocab_size, vector_size = map(int, header.split())
            binary_len = np.dtype('float32').itemsize * vector_size
            initW = np.random.uniform(-0.25,0.25,(len(self.textData.word2id), vector_size))
            for line in tqdm(range(vocab_size)):
                word = []
                while True:
                    ch = f.read(1)
                    if ch == b' ':
                        word = b''.join(word).decode('utf-8')
                        break
                    if ch != b'\n':
                        word.append(ch)
                if word in self.textData.word2id:
                    if embeddings_format == 'bin':
                        vector = np.fromstring(f.read(binary_len), dtype='float32')
                    elif embeddings_format == 'vec':
                        vector = np.fromstring(f.readline(), sep=' ', dtype='float32')
                    else:
                        raise Exception("Unkown format for embeddings: %s " % embeddings_format)
                    initW[self.textData.word2id[word]] = vector
                else:
                    if embeddings_format == 'bin':
                        f.read(binary_len)
                    elif embeddings_format == 'vec':
                        f.readline()
                    else:
                        raise Exception("Unkown format for embeddings: %s " % embeddings_format)

        # PCA Decomposition to reduce word2vec dimensionality
        if self.args.embeddingSize < vector_size:
            U, s, Vt = np.linalg.svd(initW, full_matrices=False)
            S = np.zeros((vector_size, vector_size), dtype=complex)
            S[:vector_size, :vector_size] = np.diag(s)
            initW = np.dot(U[:, :self.args.embeddingSize], S[:self.args.embeddingSize, :self.args.embeddingSize])

        # Initialize input and output embeddings
        sess.run(em_in.assign(initW))
        sess.run(em_out.assign(initW))


    def managePreviousModel(self, sess):
        """ Restore or reset the model, depending of the parameters
        If the destination directory already contains some file, it will handle the conflict as following:
         * If --reset is set, all present files will be removed (warning: no confirmation is asked) and the training
         restart from scratch (globStep & cie reinitialized)
         * Otherwise, it will depend of the directory content. If the directory contains:
           * No model files (only summary logs): works as a reset (restart from scratch)
           * Other model files, but modelName not found (surely keepAll option changed): raise error, the user should
           decide by himself what to do
           * The right model file (eventually some other): no problem, simply resume the training
        In any case, the directory will exist as it has been created by the summary writer
        Args:
            sess: The current running session
        """

        modelName = self._getModelName()

        if os.listdir(self.modelDir):
            if os.path.exists(modelName):  # Restore the model
                print('Restoring previous model from {}'.format(modelName))
                self.saver.restore(sess, modelName)  # Will crash when --reset is not activated and the model has not been saved yet
            else:  # No other model to conflict with (probably summary files)
                print('No previous model found, but some files found at {}. Cleaning...'.format(self.modelDir))  # Warning: No confirmation asked
                self.args.reset = True

        else:
            print('No previous model found, starting from clean directory: {}'.format(self.modelDir))

    def loadModelParams(self):
        """ Load the some values associated with the current model, like the current globStep value
        For now, this function does not need to be called before loading the model (no parameters restored). However,
        the modelDir name will be initialized here so it is required to call this function before managePreviousModel(),
        _getModelName() or _getSummaryName()
        Warning: if you modify this function, make sure the changes mirror saveModelParams, also check if the parameters
        should be reset in managePreviousModel
        """
        # Compute the current model path
        self.modelDir = os.path.join(self.args.rootDir, self.MODEL_DIR_BASE)
        if self.args.modelTag:
            self.modelDir += '-' + self.args.modelTag

        # If there is a previous model, restore some parameters
        configName = os.path.join(self.modelDir, self.CONFIG_FILENAME)
        # Loading
        config = configparser.ConfigParser()
        config.read(configName)

        # Check the version
        currentVersion = config['General'].get('version')
        if currentVersion != self.CONFIG_VERSION:
            raise UserWarning('Present configuration version {0} does not match {1}. You can try manual changes on \'{2}\''.format(currentVersion, self.CONFIG_VERSION, configName))

        # Restoring the the parameters
        self.globStep = config['General'].getint('globStep')
        self.args.watsonMode = config['General'].getboolean('watsonMode')
        self.args.autoEncode = config['General'].getboolean('autoEncode')
        self.args.corpus = config['General'].get('corpus')

        self.args.datasetTag = config['Dataset'].get('datasetTag')
        self.args.maxLength = config['Dataset'].getint('maxLength')  # We need to restore the model length because of the textData associated and the vocabulary size (TODO: Compatibility mode between different maxLength)
        self.args.filterVocab = config['Dataset'].getint('filterVocab')
        self.args.skipLines = config['Dataset'].getboolean('skipLines')
        self.args.vocabularySize = config['Dataset'].getint('vocabularySize')

        self.args.hiddenSize = config['Network'].getint('hiddenSize')
        self.args.numLayers = config['Network'].getint('numLayers')
        self.args.softmaxSamples = config['Network'].getint('softmaxSamples')
        self.args.initEmbeddings = config['Network'].getboolean('initEmbeddings')
        self.args.embeddingSize = config['Network'].getint('embeddingSize')
        self.args.embeddingSource = config['Network'].get('embeddingSource')

        # No restoring for training params, batch size or other non model dependent parameters

        # Show the restored params
        print()
        print('Warning: Restoring parameters:')
        print('globStep: {}'.format(self.globStep))
        print('watsonMode: {}'.format(self.args.watsonMode))
        print('autoEncode: {}'.format(self.args.autoEncode))
        print('corpus: {}'.format(self.args.corpus))
        print('datasetTag: {}'.format(self.args.datasetTag))
        print('maxLength: {}'.format(self.args.maxLength))
        print('filterVocab: {}'.format(self.args.filterVocab))
        print('skipLines: {}'.format(self.args.skipLines))
        print('vocabularySize: {}'.format(self.args.vocabularySize))
        print('hiddenSize: {}'.format(self.args.hiddenSize))
        print('numLayers: {}'.format(self.args.numLayers))
        print('softmaxSamples: {}'.format(self.args.softmaxSamples))
        print('initEmbeddings: {}'.format(self.args.initEmbeddings))
        print('embeddingSize: {}'.format(self.args.embeddingSize))
        print('embeddingSource: {}'.format(self.args.embeddingSource))
        print()

        # For now, not arbitrary  independent maxLength between encoder and decoder
        self.args.maxLengthEnco = self.args.maxLength
        self.args.maxLengthDeco = self.args.maxLength + 2


    def _getSummaryName(self):
        """ Parse the argument to decide were to save the summary, at the same place that the model
        The folder could already contain logs if we restore the training, those will be merged
        Return:
            str: The path and name of the summary
        """
        return self.modelDir

    def _getModelName(self):
        """ Parse the argument to decide were to save/load the model
        This function is called at each checkpoint and the first time the model is load. If keepAll option is set, the
        globStep value will be included in the name.
        Return:
            str: The path and name were the model need to be saved
        """
        modelName = os.path.join(self.modelDir, self.MODEL_NAME_BASE)
        if self.args.keepAll:  # We do not erase the previously saved model by including the current step on the name
            modelName += '-' + str(self.globStep)
        return modelName + self.MODEL_EXT

    def getDevice(self):
        """ Parse the argument to decide on which device run the model
        Return:
            str: The name of the device on which run the program
        """
        if self.args.device == 'cpu':
            return '/cpu:0'
        elif self.args.device == 'gpu':
            return '/gpu:0'
        elif self.args.device is None:  # No specified device (default)
            return None
        else:
            print('Warning: Error in the device name: {}, use the default device'.format(self.args.device))
            return None
