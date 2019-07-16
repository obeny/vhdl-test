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
void initSignalMap(void)
{
    memset(rtdata.signal_map, 0xFF, sizeof(rtdata.signal_map));
}

// --------------------------------------------------------------------------
bool executeTestVector(void)
{
    if (0 == rtdata.cur_vector)
        executeDefaultVector();
    
    executeVector();

    ++rtdata.cur_vector;

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
                rtdata.failed_vectors_cnt[rtdata.cur_testcase] = rtdata.failed_vectors_cnt[rtdata.cur_testcase] + 1;
        }
    }
}

// --------------------------------------------------------------------------
static void executeDefaultVector(void)
{
    for (UINT8 signal = 0; signal < rtdata.signals_cnt; ++signal)
        processSetSignal(signal, rtdata.vectors[VECTOR_DEFAULTS].content[signal]);
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
            setPinDir(rtdata.signal_map[pos], E_PINDIR_OUT);
            setPinValue(rtdata.signal_map[pos], (E_SIGVAL_SET_L == val)?(false):(true));
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
        case E_SIGVAL_SET_H:
            setPinDir(rtdata.signal_map[pos], E_PINDIR_IN);
            return (getPinValue(rtdata.signal_map[pos]) == (E_SIGVAL_EXP_L == val)?(false):(true));
    }

    return (true);
}
