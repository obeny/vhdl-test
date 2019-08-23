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

// fault handlers
__no_return void NMI_Handler(void);
__no_return void NMI_Handler(void)
{
    rtdata.error = E_ERROR_NMI;
    while (1);
}

__no_return void HardFault_Handler(void);
__no_return void HardFault_Handler(void)
{
    rtdata.error = E_ERROR_HARDFAULT;
    while (1);
}

__no_return void MemManage_Handler(void);
__no_return void MemManage_Handler(void)
{
    rtdata.error = E_ERROR_MEMMANAGE;
    while (1);
}

__no_return void BusFault_Handler(void);
__no_return void BusFault_Handler(void)
{
    rtdata.error = E_ERROR_BUSFAULT;
    while (1);
}

__no_return void UsageFault_Handler(void);
__no_return void UsageFault_Handler(void)
{
    rtdata.error = E_ERROR_USAGEFAULT;
    while (1);
}

// --------------------------------------------------------------------------
void main(void)
{
    init();

    syncTimerStart(SYNC_TIMER_1000MS);

    initRuntimeData();

    while(1)
    {
        if (checkStack(STACK_SIZE - STACK_CHECK_THRSH))
        {
            rtdata.error = E_ERROR_STACK;
            return;
        }

        syncTimerUpdate();
        if (syncTimerGetTimer(SYNC_TIMER_1000MS, SYNC_TIMER_1000MS_VAL))
            exec1();

        if (!handleCommand())
        {
            rtdata.broken_frames++;
            if (rtdata.broken_frames > BROKEN_FRAMES_LIMIT)
            {
                rtdata.error = E_ERROR_FRAME;
                return;
            }
        }
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
