Training

1. It is most likely that a training session is already taking place in the background.
    To check this run `ps -a` and locate a process with CMD=python.

2. To check the progress of the current training session, run the command `cat nohup.out` or `tail -f nohup.out`.

3. Feel free to start a new training session if you see that there is no current training session going on (step #1).

Option 1:
    We are currently training on top of a pretrained model called `opensubs`.
    To continue training the `opensubs` model, run a new trianing session with command: `nohup python ./main.py --modelTag opensubs &`

Option 2: If you want to train using custom data:
    1. Copy over your subtitles file to `scripts/data/` directory.
    2. From within the `scripts` folder, run `python data_filterer.py data/`.
    3. Rename the produced `data.txt` to some unique name (i.e. `day-custom.txt`) and copy it to `<project root dir>/data/lightweight/` folder.
    4. To continue training the existing model using the custom data, run `nohup python ./main.py --modelTag opensubs --corpus lightweight --datasetTag <dataset-tag-name> --overrideDataset &`
        i.e. If you had renamed your `data.txt` file to `day-custom.txt`, your <dataset-tag-name> would be `day-custom`
    5. Run `tail -f nohup.out` to ensure that training began successfully (if any error occurs, let me know (dayeong) and just train using option 1)
