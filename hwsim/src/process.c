#include "gpio.h"
#include "process.h"

#include <string.h>

st_rtdata_t rtdata;

// static functions
static void executeVector(void);
static void executeDefaultVector(void);

static void processSetSignal(UINT8 pos, BYTE val);
static bool processExpSignal(UINT8 pos, BYTE val);

// --------------------------------------------------------------------------
void initRuntimeData(void)
{
    memset(&rtdata, 0x00, sizeof(rtdata));
}

// --------------------------------------------------------------------------
bool executeTestVector(void)
{
    static UINT8 prev_testcase = 0;

    if (prev_testcase == rtdata.cur_testcase)
        executeDefaultVector();
    executeVector();

    ++rtdata.cur_vector;
    rtdata.prev_testcase = rtdata.cur_testcase;
    rtdata.cur_testcase = rtdata.vectors[rtdata.cur_vector].testcase;

    return (true);
}

// static functions
// --------------------------------------------------------------------------
static void executeVector(void)
{
    for (UINT8 signal = 0; signal < rtdata.signals_cnt; ++signal)
        processSetSignal(signal, rtdata.vectors[rtdata.cur_vector].content[signal]);

    if (E_COMP_TYPE_CONCURRENT == rtdata.comp_type)
    {
        for (UINT8 signal = 0; signal < rtdata.signals_cnt; ++signal)
        {
            if (!processExpSignal(signal, rtdata.vectors[rtdata.cur_vector].content[signal]))
                rtdata.vectors[rtdata.cur_vector].failed_signals |= (1 << signal);
        }
    }
    else
        return;
}

// --------------------------------------------------------------------------
static void executeDefaultVector(void)
{
    for (UINT8 signal = 0; signal < rtdata.signals_cnt; ++signal)
        processSetSignal(signal, rtdata.vectors[VECTOR_DEFAULTS_POS].content[signal]);
}

// --------------------------------------------------------------------------
static void processSetSignal(UINT8 pos, BYTE val)
{
    switch (val)
    {
        case E_SIGVAL_DC:
            break;
        case E_SIGVAL_SET_L:
        case E_SIGVAL_SET_H:
            setPinDir(pos, E_PINDIR_OUT);
            setPinValue(pos, (E_SIGVAL_SET_L == val)?(false):(true));
            break;
    }
}

// --------------------------------------------------------------------------
static bool processExpSignal(UINT8 pos, BYTE val)
{
    switch (val)
    {
        case E_SIGVAL_DC:
            break;
        case E_SIGVAL_EXP_L:
        case E_SIGVAL_EXP_H:
            setPinDir(pos, E_PINDIR_IN);
            return (getPinValue(pos) == (E_SIGVAL_EXP_L == val)?(false):(true));
    }

    return (true);
}
