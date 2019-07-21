#ifndef PROCESS_H
#define PROCESS_H

#include "global.h"
#include "platform.h"

#define SIGNAL_NO_MAPPING 0xFF
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
    E_SIGVAL_EXP_L = 'l',
    E_SIGVAL_EXP_H = 'h'
} e_sig_val;

typedef enum
{
    E_COMP_TYPE_CONCURRENT = 0,
    E_COMP_TYPE_SEQUENTIAL = 1
} e_comp_type_t;

typedef struct
{
    UINT32 interval;
    UINT8 testcase;
    BYTE content[MAX_SIGNALS];

    UINT32 failed_signals;
} __packed vector_t;

typedef struct
{
    e_comp_type_t comp_type;
    UINT8 signals_cnt;
    UINT8 vector_cnt;
    UINT8 testcase_cnt;
    UINT32 clock_period;
    UINT32 interval;

    UINT8 broken_frames;
    UINT8 cur_vector;
    UINT8 cur_testcase;
    UINT8 prev_testcase;

    vector_t vectors[MAX_VECTORS];
} st_rtdata_t;

void initRuntimeData(void);

bool executeTestVector(void);

#endif // PROCESS_H
