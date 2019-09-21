#ifndef PROCESS_H
#define PROCESS_H

#include "global.h"
#include "platform.h"

#define BROKEN_FRAMES_LIMIT 4

#define VECTOR_DEFAULTS_POS (MAX_VECTORS - 1)
#define VECTOR_DEFAULTS 0xFF
#define VECTOR_DEFAULT_INTVAL 0xFFFFFFFFUL

#if GPIO_CNT > 32
    #error "GPIO_CNT exceeds size of UINT32"
#endif

enum
{
    E_SIGVAL_DC = '-',
    E_SIGVAL_SET_L = '0',
    E_SIGVAL_SET_H = '1',
    E_SIGVAL_SET_Z = 'Z',

    E_SIGVAL_EXP_L = 'l',
    E_SIGVAL_EXP_H = 'h',
    E_SIGVAL_EXP_LZ = 'L',
    E_SIGVAL_EXP_HZ = 'H',
    E_SIGVAL_EXP_Z = 'Z',
    E_SIGVAL_EXP_X = 'X'
} e_sig_val;

enum
{
    E_ERROR_STACK = 0,
    E_ERROR_FRAME = 1,
    E_ERROR_NMI = 2,
    E_ERROR_HARDFAULT = 3,
    E_ERROR_MEMMANAGE = 4,
    E_ERROR_BUSFAULT = 5,
    E_ERROR_USAGEFAULT = 6
} e_error;

typedef enum
{
    E_COMP_TYPE_CONCURRENT = 0,
    E_COMP_TYPE_SEQUENTIAL = 1
} e_comp_type_t;

typedef enum
{
    E_CLK_DEF_L = 0,
    E_CLK_DEF_H = 1,
    E_CLK_DEF_X = 0xFF
} e_clk_def_t;

typedef struct
{
    UINT32 interval;
    UINT32 failed_signals;
    UINT8 testcase;
    BYTE content[MAX_SIGNALS];
} __packed vector_t;

typedef union
{
    struct
    {
        UINT8 remember_state : 1;
        UINT8 clock_disable  : 1;
        UINT8 clock_reset    : 1;
        UINT8 reserved       : 5;
    } flags;
    UINT8 u8;
} flags_t;

typedef struct
{
    e_comp_type_t comp_type;
    e_clk_def_t clk_def_val;

    UINT16 vector_cnt;
    UINT8 signals_cnt;
    UINT8 testcase_cnt;
    UINT8 clock_pin_pos;
    UINT32 clock_period;
    UINT32 interval;
} meta_t;

typedef struct
{
    bool cont_testcase;

    UINT32 cur_ns;
    UINT32 cur_clk_ticks;

    UINT16 total_clk_ticks_cnt;
    UINT16 cur_vector;

    UINT8 broken_frames;
    UINT8 cur_testcase;
    UINT8 prev_testcase;

    BYTE hiz[MAX_SIGNALS];

    meta_t meta;
    vector_t vectors[MAX_VECTORS];
    flags_t flags[MAX_TESTCASES];

    BYTE error;
} st_rtdata_t;

void initRuntimeData(void);

bool executeTestVector(void);

#endif // PROCESS_H
