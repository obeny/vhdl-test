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
static bool cmdHiz(void);
static bool cmdDeviceInfo(void);

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
        case E_CMD_HIZ:
            return cmdHiz();
        case E_CMD_DEVICE_INFO:
            return cmdDeviceInfo();
        default:
            break;
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
    if (!usartRead(&usart_comm, comm_buffer+1, 15, COMM_TIMEOUT))
        goto fail;

    if (checksum8Bit(comm_buffer, 15) == comm_buffer[15])
    {
        rtdata.meta.comp_type = comm_buffer[1];
        rtdata.meta.clk_def_val = comm_buffer[2];
        rtdata.meta.testcase_cnt = comm_buffer[3];
        rtdata.meta.vector_cnt = comm_buffer[4] | comm_buffer[5] << 8;
        rtdata.meta.signals_cnt = comm_buffer[6];
        rtdata.meta.clock_period = comm_buffer[7] | comm_buffer[8] << 8 | comm_buffer[9] << 16 | comm_buffer[10] << 24;
        rtdata.meta.interval = comm_buffer[11] | comm_buffer[12] << 8 | comm_buffer[13] << 16 | comm_buffer[14] << 24;
        rtdata.meta.clock_pin_pos = rtdata.meta.signals_cnt;

        if (
            rtdata.meta.testcase_cnt > MAX_TESTCASES ||
            rtdata.meta.signals_cnt > MAX_SIGNALS ||
            rtdata.meta.vector_cnt > MAX_VECTORS
        )
            goto fail;

        if (rtdata.meta.comp_type == E_COMP_TYPE_SEQUENTIAL)
        {
            setPinDir(rtdata.meta.clock_pin_pos, E_PINDIR_OUT);
            setPinValue(rtdata.meta.clock_pin_pos, rtdata.meta.clk_def_val);
        }
        else if (rtdata.meta.comp_type != E_COMP_TYPE_CONCURRENT)
            goto fail;

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

        if (0 != rtdata.flags[testcase].flags.reserved)
            goto fail;

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

    UINT16 vectors;
    UINT16 first_vector;
    UINT16 index;
    UINT8 testcase;
    UINT8 len;

    if (E_CMD_SEND_REPORT == byte)
    {
        testcase = rtdata.prev_testcase;
        for (index = 0; rtdata.vectors[index].testcase != testcase; ++index);
        first_vector = index;
        for (; (index < rtdata.meta.vector_cnt) && (rtdata.vectors[index].testcase == testcase); ++index);
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
        comm_buffer[2 + sizeof(UINT32)*index] = rtdata.total_clk_ticks_cnt & 0xFF;
        comm_buffer[2 + sizeof(UINT32)*index + 1] = (rtdata.total_clk_ticks_cnt >> 8) & 0xFF;
        comm_buffer[2 + sizeof(UINT32)*index + 2] = rtdata.cur_ns & 0xFF;
        comm_buffer[2 + sizeof(UINT32)*index + 3] = (rtdata.cur_ns >> 8) & 0xFF;
        comm_buffer[2 + sizeof(UINT32)*index + 4] = (rtdata.cur_ns >> 16) & 0xFF;
        comm_buffer[2 + sizeof(UINT32)*index + 5] = (rtdata.cur_ns >> 24) & 0xFF;
        len = 2 + 2 + 4 + (sizeof(UINT32)*vectors);
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
    UINT16 vector_num;
    UINT8 testcase_num;
    UINT8 payload_size =
        sizeof(vector_num) + sizeof(testcase_num) + sizeof(rtdata.vectors[0].interval) + rtdata.meta.signals_cnt;

    if (!usartRead(&usart_comm, comm_buffer+1, payload_size+1, COMM_TIMEOUT))
        goto fail;

    if (checksum8Bit(comm_buffer, payload_size+1) == comm_buffer[payload_size+1])
    {
        vector_num = comm_buffer[1] | comm_buffer[2] << 8;
        testcase_num = comm_buffer[3];
        interval = comm_buffer[4] | comm_buffer[5] << 8 | comm_buffer[6] << 16 | comm_buffer[7] << 24;

        if (!((vector_num == VECTOR_DEFAULTS) && (VECTOR_DEFAULT_INTVAL == interval)))
        {
            if (vector_num > rtdata.meta.vector_cnt)
                goto fail;
        }
        else
            vector_num = VECTOR_DEFAULTS_POS;

        memcpy(&rtdata.vectors[vector_num].content, &comm_buffer[8], rtdata.meta.signals_cnt);
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

// --------------------------------------------------------------------------
static bool cmdHiz(void)
{
    UINT8 signal;
    UINT8 hiz;

    if (!usartRead(&usart_comm, comm_buffer+1, 3, COMM_TIMEOUT))
        goto fail;

    if (checksum8Bit(comm_buffer, 3) == comm_buffer[3])
    {
        signal = comm_buffer[1];
        hiz = comm_buffer[2];
        rtdata.hiz[signal] = hiz;

        usartSendByte(&usart_comm, 'O');
        return (true);
    }
fail:
    usartSendByte(&usart_comm, 'F');
    return (false);
}

// --------------------------------------------------------------------------
static bool cmdDeviceInfo(void)
{
    UINT8 payload_len;

    UINT8 byte = usartReadByte(&usart_comm);
    if (E_CMD_DEVICE_INFO == byte)
    {
        usartSendByte(&usart_comm, 'O');

        comm_buffer[1] = GPIO_CNT;
        comm_buffer[2] = MAX_TESTCASES;
        comm_buffer[3] = (uint16_t)(MAX_VECTORS) & 0xFF;
        comm_buffer[4] = ((uint16_t)(MAX_VECTORS) >> 8) & 0xFF;
        comm_buffer[5] = VERSION_NUM;
        comm_buffer[6] = strlen(FVERSION);

        memset((void *)(comm_buffer+7), 0x00, PLATFORM_NAME_LEN);
        strncpy((char*)(comm_buffer+7), FVERSION, PLATFORM_NAME_LEN);
        payload_len = 7 + PLATFORM_NAME_LEN;
        comm_buffer[payload_len] = checksum8Bit(comm_buffer, payload_len);
        usartSend(&usart_comm, comm_buffer, payload_len+1);
        return (true);
    }
    usartSendByte(&usart_comm, 'F');
    return (false);
}
