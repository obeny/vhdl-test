#ifndef COMM_H
#define COMM_H

#include "global.h"
#include "usart.h"

#define BUFFER_SIZE 128
#define COMM_TIMEOUT 5000

enum command_e
{
    E_CMD_RESET = 'r',
    E_CMD_SET_COMP_TYPE = 't',
    E_CMD_MAP_SIGNAL = 'm',
    E_CMD_SET_TC_NAME = 'n',
    E_CMD_SEND_REPORT = 's',
    E_CMD_SET_META = 'i',
    E_CMD_CFG_VECTOR = 'v',
    E_CMD_EXECUTE = 'e'
};

bool handleCommand();

#endif // COMM_H
