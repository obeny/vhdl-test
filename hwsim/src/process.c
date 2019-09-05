#include "gpio.h"
#include "process.h"

#include <string.h>
#include <stdfix.h>

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
    if (!rtdata.cont_testcase)
    {
        rtdata.cont_testcase = true;

        // reset signals if != remember_state through default vector
        if (!rtdata.flags[rtdata.cur_testcase].flags.remember_state)
            executeDefaultVector();

        // reset clock if = clock_reset
        if (rtdata.flags[rtdata.cur_testcase].flags.clock_reset)
        {
            rtdata.cur_clk_ticks = 0;
            rtdata.cur_ns = 0;

            if (E_CLK_DEF_H == rtdata.meta.clk_def_val)
                setPinValue(rtdata.meta.clock_pin_pos, true);
            else
                setPinValue(rtdata.meta.clock_pin_pos, false);
        }
    }
    executeVector();

    ++rtdata.cur_vector;
    rtdata.prev_testcase = rtdata.cur_testcase;
    rtdata.cur_testcase = rtdata.vectors[rtdata.cur_vector].testcase;
    // new testcase started
    if (rtdata.cur_testcase != rtdata.prev_testcase)
        rtdata.cont_testcase = false;

    return (true);
}

// static functions
// --------------------------------------------------------------------------
static void executeVector(void)
{
    UINT32 clk_ticks;
    UINT32 tick;

    for (UINT8 signal = 0; signal < rtdata.meta.signals_cnt; ++signal)
        processSetSignal(signal, rtdata.vectors[rtdata.cur_vector].content[signal]);

    if (E_COMP_TYPE_SEQUENTIAL == rtdata.meta.comp_type)
    {
        rtdata.cur_ns += rtdata.vectors[rtdata.cur_vector].interval;
        clk_ticks = (rtdata.cur_ns * 1000) - 1;
        clk_ticks = clk_ticks / rtdata.meta.clock_period;
        clk_ticks = clk_ticks - rtdata.cur_clk_ticks;
        rtdata.cur_clk_ticks += clk_ticks;
        if (!rtdata.flags[rtdata.cur_testcase].flags.clock_disable)
        {
            rtdata.total_clk_ticks_cnt += clk_ticks;

            for (tick = 0; tick < clk_ticks; ++tick)
                tickClock(rtdata.meta.clock_pin_pos);
        }
    }

    for (UINT8 signal = 0; signal < rtdata.meta.signals_cnt; ++signal)
    {
        if (!processExpSignal(signal, rtdata.vectors[rtdata.cur_vector].content[signal]))
            rtdata.vectors[rtdata.cur_vector].failed_signals |= (1 << signal);
    }
}

// --------------------------------------------------------------------------
static void executeDefaultVector(void)
{
    for (UINT8 signal = 0; signal < rtdata.meta.signals_cnt; ++signal)
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
        case E_SIGVAL_SET_Z:
        case E_SIGVAL_SET_X:
            setPinDir(pos, E_PINDIR_IN);
            break;
        default:
            break;
    }
}

// --------------------------------------------------------------------------
static bool processExpSignal(UINT8 pos, BYTE val)
{
    bool res, exp;
    bool z_l, z_h;

    switch (val)
    {
        case E_SIGVAL_DC:
            break;
        case E_SIGVAL_EXP_L:
        case E_SIGVAL_EXP_LZ:
        case E_SIGVAL_EXP_H:
        case E_SIGVAL_EXP_HZ:
        {
            setPinDir(pos, E_PINDIR_IN);
            res = getPinValue(pos);
            if ((E_SIGVAL_EXP_L == val) || (E_SIGVAL_EXP_LZ == val))
                exp = false;
            else
                exp = true;
            if (res == exp)
                return (true);
            return (false);
        }
        case E_SIGVAL_EXP_Z:
        {
            if (0x00 == rtdata.hiz[pos])
                return (true);
            setPinDir(pos, E_PINDIR_IN);
            setPinDir(rtdata.hiz[pos], E_PINDIR_OUT);
            setPinValue(rtdata.hiz[pos], false);
            z_l = getPinValue(pos);
            setPinValue(rtdata.hiz[pos], true);
            z_h = getPinValue(pos);
            setPinDir(rtdata.hiz[pos], E_PINDIR_IN);
            if ((false == z_l) && (true == z_h))
                return (true);
            return (false);
        }
        default:
            break;
    }

    return (true);
}
