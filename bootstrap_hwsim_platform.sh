#!/bin/bash

if [ $# == 1 ]; then
    PLATFORM=${1}
    echo "Bootstraping \"${PLATFORM}\" platform"
else
    echo "No platform given, exitting..."
    exit 1
fi

set -e

ARCH=`echo ${PLATFORM} | cut -f 1 -d "_"`
LIBARCH="lib_${ARCH}"
LIBARCH_REPO="http://obeny.obeny.net/svn/${LIBARCH}/trunk"

function svn_checkout_repo()
{
    REPO_NAME=${1}
    REPO_URL=${2}
    REPO_PATH=${3}

    if [ ! -e "${REPO_PATH}" ]
    then
	echo ">>> (SVN) Checking out '${REPO_NAME}' repo..."
	svn checkout ${REPO_URL} ${REPO_PATH}
    else
	echo ">>> (SVN) Repo '${REPO_NAME}' already checked out..."
    fi
}

# checkout lib_at91sam7
svn_checkout_repo "${LIBARCH}" ${LIBARCH_REPO} "hwsim/platforms/${PLATFORM}/${LIBARCH}"
