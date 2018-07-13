#!/bin/bash
if [ "$1" == "-h" ]; then
    echo "Run \"./copy-checkpoint-from-p2.sh <path-to-gpu.pem> <model-name>\""
    echo "<path-to-gpu.pem>: Path to gpu.pem file"
    echo "<model-name>: model name in save/ (i.e. opensubs)"
elif [ "$1" != "" ] && [ "$2" != "" ]; then
    echo "Copying over checkpoints for model - " $2
    scp -i $1 -r ec2-user@ec2-13-59-254-58.us-east-2.compute.amazonaws.com:Felix.AI/save/model-$2 ./save/
else
    echo "Run \"./copy-checkpoint-from-p2.sh -h\" for help"
fi
echo ""
