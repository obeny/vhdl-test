#!/bin/bash

if [[ $# != 1 ]]
then
    echo "Usage: _del_files.sh <directory_with_tests>"
    exit 1
fi

DIR=${1}
echo "Removing TESTBENCHES from ${DIR}..."
for I in `find ${DIR}/tb -type f`
do
    echo -e "\t${I}"
    rm tb/`basename ${I}`
done

echo -e "\nRemoving COMPONENT SOURCES from ${DIR}..."
for I in `find ${DIR}/src -type f`
do
    echo -e "\t${I}"
    rm src/`basename ${I}`
done

echo -e "\nRemoving TEST SCRIPTS from ${DIR}..."
for I in `find ${DIR}/scripts -type f`
do
    echo -e "\t${I}"
    rm scripts/`basename ${I}`
done
