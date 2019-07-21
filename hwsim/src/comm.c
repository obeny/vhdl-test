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
        usartSendByte(&usart_comm, 'O');
        return (true);
    }
    usartSendByte(&usart_comm, 'F');
    return (false);
}

// --------------------------------------------------------------------------
static bool cmdSetMeta(void)
{
    if (!usartRead(&usart_comm, comm_buffer+1, 13, COMM_TIMEOUT))
        goto fail;

    if (checksum8Bit(comm_buffer, 13) == comm_buffer[13])
    {
        rtdata.comp_type = comm_buffer[1];
        rtdata.testcase_cnt = comm_buffer[2];
        rtdata.vector_cnt = comm_buffer[3];
        rtdata.signals_cnt = comm_buffer[4];
        rtdata.clock_period = comm_buffer[5] | comm_buffer[6] << 8 | comm_buffer[7] << 16 | comm_buffer[8] << 24;
        rtdata.interval = comm_buffer[9] | comm_buffer[10] << 8 | comm_buffer[11] << 16 | comm_buffer[12] << 24;

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
        comm_buffer[1] = rtdata.failed_testcase_cnt;
        comm_buffer[2] = rtdata.broken_frames;
        for (testcase_num = 0; testcase_num < rtdata.testcase_cnt; ++testcase_num)
            comm_buffer[3 + testcase_num] = rtdata.failed_vectors_cnt[testcase_num];
        comm_buffer[rtdata.testcase_cnt+3] = checksum8Bit(comm_buffer, rtdata.testcase_cnt+3);

        usartSendByte(&usart_comm, 'O');
        usartSend(&usart_comm, comm_buffer, testcase_num+4);
        return (true);
    }
    usartSendByte(&usart_comm, 'F');
    return (false);
}

// --------------------------------------------------------------------------
static bool cmdConfigVector(void)
{
    UINT8 vector_num;
    UINT8 payload_size = sizeof(vector_num) + sizeof(rtdata.vectors[0].interval) + rtdata.signals_cnt ;
    UINT32 interval;

    if (!usartRead(&usart_comm, comm_buffer+1, payload_size+1, COMM_TIMEOUT))
        goto fail;

    if (checksum8Bit(comm_buffer, payload_size+1) == comm_buffer[payload_size+1])
    {
        vector_num = comm_buffer[1];
        interval = comm_buffer[2] | comm_buffer[3] << 8 | comm_buffer[4] << 16 | comm_buffer[5] << 24;

        if (!((vector_num == VECTOR_DEFAULTS) && (VECTOR_DEFAULT_INTVAL == interval)))
        {
            if (vector_num > MAX_VECTORS)
                goto fail;
        }
        else
            vector_num = VECTOR_DEFAULTS_POS;

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
