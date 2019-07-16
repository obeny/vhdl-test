#ifndef PROCESS_H
#define PROCESS_H

#include "global.h"
#include "platform.h"

#define SIGNAL_NO_MAPPING 0xFF
#define VECTOR_DEFAULTS (MAX_VECTORS - 1)
#define VECTOR_DEFAULT_INTVAL 0xFFFFFFFFUL

typedef enum
{
    E_COMP_TYPE_CONCURRENT = 0,
    E_COMP_TYPE_SEQUENTIAL = 1
} e_comp_type_t;

typedef struct
{
    UINT32 interval;
    BYTE content[MAX_SIGNALS];
} vector_t;

typedef struct
{
    e_comp_type_t comp_type;
    UINT8 signals_cnt;
    UINT8 vector_cnt;
    UINT8 testcase_cnt;
    UINT8 broken_frames;
    UINT8 failed_testcase_cnt;
    UINT8 signal_map[MAX_SIGNALS];
    UINT8 failed_vectors_cnt[MAX_TESTCASES];
    BYTE tc_name[MAX_TESTCASES][TC_NAME_LEN];
    vector_t vectors[MAX_VECTORS];
    UINT32 clock_period;
    UINT32 interval;

    UINT8 cur_vector;
    UINT8 cur_testcase;
} st_rtdata_t;

void initRuntimeData(void);
void initSignalMap(void);

bool executeTestVector(void);

#endif // PROCESS_H
