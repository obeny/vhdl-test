#!/bin/bash

if [[ $# != 1 ]]
then
    echo "Usage: _add_files.sh <directory_with_tests>"
    exit 1
fi

DIR=${1}
echo "Inserting TESTBENCHES from ${DIR}..."
for I in `find ${DIR}/tb -type f`
do
    echo -e "\t${I}"
    ln -snf `readlink -f ${I}` tb/`basename ${I}`
done

echo -e "\nInserting COMPONENT SOURCES from ${DIR}..."
for I in `find ${DIR}/src -type f`
do
    echo -e "\t${I}"
    ln -snf `readlink -f ${I}` src/`basename ${I}`
done

echo -e "\nInserting TEST SCRIPTS from ${DIR}..."
for I in `find ${DIR}/scripts -type f`
do
    echo -e "\t${I}"
    ln -snf `readlink -f ${I}` scripts/`basename ${I}`
done
