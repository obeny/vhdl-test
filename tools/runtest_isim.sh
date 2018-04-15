#!/bin/bash

# helper functions
function print_msg() {
    [[ ! -z "${VERB}" ]] && echo "$1"
}

# arguments assignment
PROG="${1}"
CMDS="${2}"
LOGD="${3}"
VERB="${4}"

COMP="$(basename ${PROG%.exe})"
OUTP=$(mktemp)

# info
print_msg "PROG: ${PROG}"
print_msg "CMDS: ${CMDS}"
print_msg "LOGD: ${LOGD}"

print_msg "COMP: ${COMP}"
print_msg "OUTP: ${OUTP}"

# check commandline arguments
if [ $# -lt 3  ]
then
    echo "usage: runtest_isim.sh <prog> <cmds> <logd> [<verb>]"
    exit -1
fi

# entry
ERR_CODE=0
ERR_FILTER="error:\|failure:"
FINISH_FILTER="TESTBENCH FINISHED"

${PROG} -tclbatch ${CMDS} -nolog > ${OUTP}

if [ ! -z "$(grep -i ${ERR_FILTER} ${OUTP})" ]
then
    grep -i ${ERR_FILTER} ${OUTP} > ${OUTP}.err
    ERR_CODE=1
else
    if [ -z "$(grep "${FINISH_FILTER}" ${OUTP})" ]
    then
	echo "ERROR: Testbench didn't reach end!" > ${OUTP}.err
	ERR_CODE=2
    fi
fi

# cleanup
mkdir -p ${LOGD}
mv ${OUTP} ${LOGD}/${COMP}.log 2> /dev/null
rm -f ${LOGD}/${COMP}.err 2> /dev/null
mv ${OUTP}.err ${LOGD}/${COMP}.err 2> /dev/null

exit ${ERR_CODE}
