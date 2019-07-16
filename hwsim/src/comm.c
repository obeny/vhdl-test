#include "config.h"
#include "chksum.h"
#include "usart.h"

#include "comm.h"
#include "gpio.h"
#include "process.h"

#include <string.h>

static BYTE comm_buffer[BUFFER_SIZE];

extern usart_cfg_st usart_comm;
extern st_rtdata_t rtdata;

// static functions
static bool cmdReset(void);
static bool cmdSetCompType(void);
static bool cmdTestcaseName(void);
static bool cmdMapSignal(void);
static bool cmdSendReport(void);
static bool cmdSetMeta(void);
static bool cmdConfigVector(void);

static bool cmdExecute(void);

// --------------------------------------------------------------------------
bool handleCommand(void)
{
    if (usartUnreadBytes(&usart_comm))
        comm_buffer[0] = usartReadByte(&usart_comm);
    else
        return (true);

    switch (comm_buffer[0])
    {
        case E_CMD_RESET:
            return cmdReset();
        case E_CMD_SET_COMP_TYPE:
            return cmdSetCompType();
        case E_CMD_SET_TC_NAME:
            return cmdTestcaseName();
        case E_CMD_MAP_SIGNAL:
            return cmdMapSignal();
        case E_CMD_CFG_VECTOR:
            return cmdConfigVector();
        case E_CMD_EXECUTE:
            return cmdExecute();
        case E_CMD_SEND_REPORT:
            return cmdSendReport();
        case E_CMD_SET_META:
            return cmdSetMeta();
    }
    usartFlush(&usart_comm);
    usartSendByte(&usart_comm, '?');
    return (false);
}

// static functions
// --------------------------------------------------------------------------
static bool cmdReset(void)
{
    UINT8 byte = usartReadByte(&usart_comm);
    if (E_CMD_RESET == byte)
    {
        resetIo();
        initRuntimeData();
        initSignalMap();
        usartSendByte(&usart_comm, 'O');
        return (true);
    }
    usartSendByte(&usart_comm, 'F');
    return (false);
}

// --------------------------------------------------------------------------
static bool cmdSetCompType(void)
{
    if (!usartRead(&usart_comm, comm_buffer+1, 2, COMM_TIMEOUT))
        goto fail;

    if (checksum8Bit(comm_buffer, 2) == comm_buffer[2])
    {
        if (comm_buffer[1] == E_COMP_TYPE_CONCURRENT || comm_buffer[1] == E_COMP_TYPE_SEQUENTIAL)
        {
            rtdata.comp_type = comm_buffer[1];
            usartSendByte(&usart_comm, 'O');
            return (true);
        }
    }
fail:
    usartSendByte(&usart_comm, 'F');
    return (false);
}

// --------------------------------------------------------------------------
static bool cmdTestcaseName(void)
{
    UINT8 len = usartReadByte(&usart_comm);
    UINT8 tc = usartReadByte(&usart_comm);

    if (!usartRead(&usart_comm, comm_buffer+3, len, COMM_TIMEOUT))
        goto fail;

    comm_buffer[1] = len;
    comm_buffer[2] = tc;

    if (checksum8Bit(comm_buffer, len+1) == comm_buffer[len+3])
    {
        strncpy((char*)&rtdata.tc_name[tc][0], (char*)comm_buffer+3, len);
        usartSendByte(&usart_comm, 'O');
        return (true);
    }
fail:
    usartSendByte(&usart_comm, 'F');
    return (false);
}

// --------------------------------------------------------------------------
static bool cmdMapSignal(void)
{
    if (!usartRead(&usart_comm, comm_buffer+1, 3, COMM_TIMEOUT))
        goto fail;

    if (checksum8Bit(comm_buffer, 3) == comm_buffer[3])
    {
        rtdata.signal_map[comm_buffer[1]] = comm_buffer[2];
        usartSendByte(&usart_comm, 'O');
        return (true);
    }
fail:
    usartSendByte(&usart_comm, 'F');
    return (false);
}

// --------------------------------------------------------------------------
static bool cmdSetMeta(void)
{
    if (!usartRead(&usart_comm, comm_buffer+1, 12, COMM_TIMEOUT))
        goto fail;

    if (checksum8Bit(comm_buffer, 12) == comm_buffer[12])
    {
        rtdata.testcase_cnt = comm_buffer[1];
        rtdata.vector_cnt = comm_buffer[2];
        rtdata.signals_cnt = comm_buffer[3];
        rtdata.clock_period = comm_buffer[4] | comm_buffer[5] << 8 | comm_buffer[6] << 16 | comm_buffer[7] << 24;
        rtdata.interval = comm_buffer[8] | comm_buffer[9] << 8 | comm_buffer[10] << 16 | comm_buffer[11] << 24;

        usartSendByte(&usart_comm, 'O');
        return (true);
    }
fail:
    usartSendByte(&usart_comm, 'F');
    return (false);
}

// --------------------------------------------------------------------------
static bool cmdSendReport(void)
{
    UINT8 testcase_num;

    UINT8 byte = usartReadByte(&usart_comm);
    if (E_CMD_SEND_REPORT == byte)
    {
        comm_buffer[1] = rtdata.testcase_cnt;
        comm_buffer[2] = rtdata.failed_testcase_cnt;
        comm_buffer[3] = rtdata.broken_frames;
        comm_buffer[4] = rtdata.vector_cnt;
        for (testcase_num = 0; testcase_num < rtdata.testcase_cnt; ++testcase_num)
            comm_buffer[5 + testcase_num] = rtdata.failed_vectors_cnt[testcase_num];
        comm_buffer[testcase_num+5] = checksum8Bit(comm_buffer, testcase_num+5);

        usartSendByte(&usart_comm, 'O');
        usartSend(&usart_comm, comm_buffer, testcase_num+6);
        return (true);
    }
    usartSendByte(&usart_comm, 'F');
    return (false);
}

// --------------------------------------------------------------------------
static bool cmdConfigVector(void)
{
    UINT8 signal_cnt = rtdata.signals_cnt;
    UINT8 vector_size = sizeof(rtdata.vectors[0].interval);
    UINT8 payload_size = vector_size + signal_cnt;
    UINT8 vector_num;
    UINT32 interval;

    if (!usartRead(&usart_comm, comm_buffer+1, payload_size, COMM_TIMEOUT))
        goto fail;

    if (checksum8Bit(comm_buffer, payload_size+1) == comm_buffer[payload_size+1])
    {
        interval = comm_buffer[2] | comm_buffer[3] << 8 | comm_buffer[4] << 16 | comm_buffer[5] << 24;
        vector_num = comm_buffer[1];

        if (!((vector_num == VECTOR_DEFAULTS) && (VECTOR_DEFAULT_INTVAL == interval)))
        {
            if (vector_num > MAX_VECTORS)
                goto fail;
        }

        memcpy(&rtdata.vectors[vector_num].content, &comm_buffer[5], sizeof(rtdata.vectors[0].content));
        rtdata.vectors[vector_num].interval = interval;

        usartSendByte(&usart_comm, 'O');
        return (true);
    }
fail:
    usartSendByte(&usart_comm, 'F');
    return (false);
}

// --------------------------------------------------------------------------
static bool cmdExecute(void)
{
    UINT8 byte = usartReadByte(&usart_comm);
    if (E_CMD_EXECUTE == byte)
    {
        if (executeTestVector())
        {
            usartSendByte(&usart_comm, 'O');
            return (true);
        }
    }
    usartSendByte(&usart_comm, 'F');
    return (false);
}
