#!/bin/bash
if [ "$1" == "-h" ]; then
    echo "Run \"./copy-dataset-to-p2.sh <path-to-gpu.pem> <dataset-dir-name>\""
    echo "<path-to-gpu.pem>: Path to gpu.pem file"
    echo "<dataset-dir-name>: dataset dir name in scripts/ (i.e. data)"
elif [ "$1" != "" ] && [ "$2" != "" ]; then
    echo "Copying over dataset in dir with name - " $2
    scp -i $1 -r  ./scripts/$2 ec2-user@ec2-13-59-254-58.us-east-2.compute.amazonaws.com:Felix.AI/scripts/$2
else
    echo "Run \"./copy-dataset-to-p2.sh -h\" for help"
fi
echo ""
