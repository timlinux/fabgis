#!/bin/bash

echo "Have you updated changelog?"
echo "Have you updated the version in setup.py?"
echo "Have you updated README & Docs?"
read -sn 1 -p "Press any key to continue..."
python setup.py sdist upload
