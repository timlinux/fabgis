#!/bin/bash
FABRICMIN=1.6.0
FABTOOMIN=0.13.0
if [ -z `which pip 2>/dev/null` ]; then sudo apt-get install python-pip; fi
if [ -z `pip freeze | grep Fabric` ]
    then
        sudo pip install fabric
    else
        VERSION=`pip freeze | grep Fabric`
        FABRICVER=`(echo ${VERSION#*=} | cut -f2 -d= )`
        if [[ $FABRICVER < $FABRICMIN ]]
            then
                echo Your Version of Fabric is $FABRICVER but you must
                echo have at least Version 1.6.0 of Fabric installed
        fi
fi
if [ -z `pip freeze | grep fabtools` ]
    then
        sudo pip install fabtools
    else
        VERSION=`pip freeze | grep fabtools`
        FABTOOVER=`(echo ${VERSION#*=} | cut -f2 -d= )`
        if [[ $FABTOOVER < $FABTOOMIN ]]
            then
                echo Your Version of fabtools is $FABTOOVER but you must
                echo have at least Versgrant all on schema publicion 0.13.0 of Fabric installed
        fi
fi
if [ -z `which git 2>/dev/null` ]; then sudo apt-get install git; fi
echo Checking for local ssh-server needs root access
if [ -z `sudo which sshd 2>/dev/null` ]; then sudo apt-get install openssh-server; fi
if [ ! -d $HOME/fabgis ]; then git clone git://github.com/timlinux/fabgis; fi
cd $HOME/fabgis
fab -H localhost fabgis.fabgis.setup_qgis2_and_postgis
