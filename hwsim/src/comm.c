#include "config.h"
#include "chksum.h"
#include "usart.h"
#include "util.h"

#include "comm.h"
#include "gpio.h"
#include "process.h"

#include <string.h>

static BYTE comm_buffer[BUFFER_SIZE];

extern usart_cfg_st usart_comm;
extern st_rtdata_t rtdata;

// static functions
static bool cmdReset(void);
static bool cmdCpuReset(void);
static bool cmdSendReport(void);
static bool cmdSetMeta(void);
static bool cmdSetFlags(void);
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
        case E_CMD_CPU_RESET:
            return cmdCpuReset();
        case E_CMD_CFG_VECTOR:
            return cmdConfigVector();
        case E_CMD_EXECUTE:
            return cmdExecute();
        case E_CMD_SEND_REPORT:
            return cmdSendReport();
        case E_CMD_SET_META:
            return cmdSetMeta();
        case E_CMD_SET_FLAGS:
            return cmdSetFlags();
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
static bool cmdCpuReset(void)
{
    UINT8 byte = usartReadByte(&usart_comm);
    if (E_CMD_CPU_RESET == byte)
    {
        usartSendByte(&usart_comm, 'O');
        delayMs(100);
        softReset();
        // should not enter this
        return (false);
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
static bool cmdSetFlags(void)
{
    UINT8 testcase;
    flags_t flags;

    if (!usartRead(&usart_comm, comm_buffer+1, 3, COMM_TIMEOUT))
        goto fail;

    if (checksum8Bit(comm_buffer, 3) == comm_buffer[3])
    {
        testcase = comm_buffer[1];
        flags.u8 = comm_buffer[2];
        rtdata.flags[testcase] = flags;

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
    UINT8 byte = usartReadByte(&usart_comm);

    UINT8 testcase;
    UINT8 first_vector;
    UINT8 vectors;
    UINT8 index;
    UINT8 len;

    if (E_CMD_SEND_REPORT == byte)
    {
        testcase = rtdata.prev_testcase;
        for (index = 0; rtdata.vectors[index].testcase != testcase; ++index);
        first_vector = index;
        for (; (index < rtdata.vector_cnt) && (rtdata.vectors[index].testcase == testcase); ++index);
        vectors = index - first_vector;
        usartSendByte(&usart_comm, 'O');

        comm_buffer[1] = vectors;
        for (index = 0; index < vectors; ++index)
        {
            UINT8 buff_pos = 2 + (sizeof(UINT32) * index);
            comm_buffer[buff_pos] = rtdata.vectors[first_vector + index].failed_signals & 0xFF;
            comm_buffer[buff_pos+1] = (rtdata.vectors[first_vector + index].failed_signals >> 8) & 0xFF;
            comm_buffer[buff_pos+2] = (rtdata.vectors[first_vector + index].failed_signals >> 16) & 0xFF;
            comm_buffer[buff_pos+3] = (rtdata.vectors[first_vector + index].failed_signals >> 24) & 0xFF;
        }
        len = 2+(sizeof(UINT32)*vectors);
        comm_buffer[len] = checksum8Bit(comm_buffer, len);

        usartSend(&usart_comm, comm_buffer, len+1);
        return (true);
    }
    usartSendByte(&usart_comm, 'F');
    return (false);
}

// --------------------------------------------------------------------------
static bool cmdConfigVector(void)
{
    UINT32 interval;
    UINT8 vector_num;
    UINT8 testcase_num;
    UINT8 payload_size =
        sizeof(vector_num) + sizeof(testcase_num) + sizeof(rtdata.vectors[0].interval) + rtdata.signals_cnt;

    if (!usartRead(&usart_comm, comm_buffer+1, payload_size+1, COMM_TIMEOUT))
        goto fail;

    if (checksum8Bit(comm_buffer, payload_size+1) == comm_buffer[payload_size+1])
    {
        vector_num = comm_buffer[1];
        testcase_num = comm_buffer[2];
        interval = comm_buffer[3] | comm_buffer[4] << 8 | comm_buffer[5] << 16 | comm_buffer[6] << 24;

        if (!((vector_num == VECTOR_DEFAULTS) && (VECTOR_DEFAULT_INTVAL == interval)))
        {
            if (vector_num > rtdata.vector_cnt)
                goto fail;
        }
        else
            vector_num = VECTOR_DEFAULTS_POS;

        memcpy(&rtdata.vectors[vector_num].content, &comm_buffer[7], rtdata.signals_cnt);
        rtdata.vectors[vector_num].interval = interval;
        rtdata.vectors[vector_num].testcase = testcase_num;

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
