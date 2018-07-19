# Training: make sure you're ssh'd into p2

1. Activate anaconda by running the command `source activate tensorflow`

2. It is most likely that a training session is already taking place in the background.
... To check this run `ps -a` and locate a process with CMD=python.

3. To check the progress of the current training session, run the command `cat nohup.out` or `tail -f nohup.out`.

4. Feel free to start a new training session if you see that there is no current training session going on (step #1).
* Option 1:
    1. We are currently training on top of a pretrained model called `opensubs`.

    2. To continue training the `opensubs` model, run a new trianing session with command: `nohup python ./main.py --modelTag opensubs &`

* Option 2: If you want to train using custom data:
    1. Copy over your subtitles file to `scripts/data/` directory.

    2. From within the `scripts` folder, run `python data_filterer.py data/`.

    3. Rename the produced `data.txt` to `<unique-tag>`.txt (i.e. <unique-tag> could be "day-custom", then your file would be reanmed to `day-custom.txt`).

    4. Copy the renamed text file to `<project root dir>/data/lightweight/` folder.

    5. In `<project root dir>/data/sample`, remove any old datasets with the same name as current dataset name (i.e. `rm dataset-lightweight-<unique-tag>*.pkl`)

    6. To continue training the existing model using the custom data, run `nohup python ./main.py --modelTag opensubs --corpus lightweight --datasetTag <unique-tag> --overrideDataset &`.

        If you had renamed your `data.txt` file to `day-custom.txt`, your <unique-tag> would be `day-custom`.

    7. Run `tail -f nohup.out` to ensure that training began successfully (if any error occurs, let me know (dayeong) and just train using option 1)


# Testing: make sure you're on your local machine

Prerequisites: Set up Tensorflow using Anaconda on your local machine https://www.tensorflow.org/install/install_mac#installing_with_anaconda

1. Activate anaconda by running the command `source activate tensorflow`

2. Run `copy-checkpoint-from-p2.sh -h` and follow the instructions to copy over saved model from p2.

3. Run `./main.py --modelTag <copied-model-name> --test interactive`

4. Run `./api.py --modelTag <saved-model-name>`
