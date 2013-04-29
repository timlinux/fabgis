#!/bin/bash

vagrant up
fab vagrant show_environment
fab vagrant install_qgis1_8
fab vagrant install_qgis2
