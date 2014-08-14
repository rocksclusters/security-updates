#!/bin/bash

# top roll directory
basedir=/state/partition1/site-roll/rocks/src/roll/security-updates

# archive rpms directory
archivedir=$basedir/archive-RPMS

for arch in "x86_64" "i686" "noarch" ; do
    if [ -d $basedir/RPMS/$arch ]; then
        if [ "$(/bin/ls $basedir/RPMS/$arch)" ]; then
            /bin/mv $basedir/RPMS/$arch/* $archivedir/$arch
        fi
    fi

done



