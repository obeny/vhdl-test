#ifndef COMM_H
#define COMM_H

#include "global.h"
#include "usart.h"

#define BUFFER_SIZE 256
#define COMM_TIMEOUT 5000

enum command_e
{
    E_CMD_RESET = 'r',
    E_CMD_CPU_RESET = 'R',
    E_CMD_SEND_REPORT = 's',
    E_CMD_SET_META = 'i',
    E_CMD_CFG_VECTOR = 'v',
    E_CMD_EXECUTE = 'e'
};

bool handleCommand();

#endif // COMM_H
