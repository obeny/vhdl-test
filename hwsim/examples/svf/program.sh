#!/bin/bash

if [ $# != 1 ];
then
    echo "usage: program.sh <comp>"
    exit -1
fi

VARIANT=${1}

openocd \
-f /opt/tc_arm-none-eabi/share/openocd/scripts/interface/ftdi/jtagkey.cfg \
-c "adapter_khz 100" \
-c "transport select jtag" \
-c "jtag newtap epm tap -expected-id 0x020a30dd -irlen 10" \
-f commands_${VARIANT}.ocd
