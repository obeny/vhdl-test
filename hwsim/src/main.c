/***************************************************************************
 *      INCLUDES
 ***************************************************************************/

#include "config.h"

#include "sync_timer.h"
#include "usart.h"
#include "util.h"

#include "comm.h"
#include "platform.h"
#include "process.h"

/***************************************************************************
 *      DEFINITIONS
 ***************************************************************************/

usart_cfg_st usart_comm;

extern st_rtdata_t rtdata;

// external functions
void initPeripherialStructures(void);
void exec1(void);

// static functions
static void init(void);


 /***************************************************************************
 *      FUNCTIONS
 ***************************************************************************/

// --------------------------------------------------------------------------
void main(void)
{
    init();

    syncTimerStart(SYNC_TIMER_1000MS);

    initRuntimeData();

    while(1)
    {
        if (checkStack(STACK_SIZE - STACK_CHECK_THRSH))
            return;

        syncTimerUpdate();
        if (syncTimerGetTimer(SYNC_TIMER_1000MS, SYNC_TIMER_1000MS_VAL))
            exec1();

        if (!handleCommand())
            rtdata.broken_frames++;
    }
}

// static functions
// --------------------------------------------------------------------------
static void init(void)
{
    initPeripherialStructures();
    usartInit(&usart_comm, USART_COMM_BAUDRATE, false, USART_PARITY_NONE);
    syncTimerInit();
}

// END
