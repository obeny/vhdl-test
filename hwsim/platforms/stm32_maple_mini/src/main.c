/***************************************************************************
 *      INCLUDES
 ***************************************************************************/

#include "config.h"

#include "io.h"
#include "sync_timer.h"
#include "usart.h"
#include "util.h"

#include "comm.h"
#include "process.h"

#include "stm32f10x_gpio.h"

#include <string.h>


/***************************************************************************
 *      DEFINITIONS
 ***************************************************************************/

usart_cfg_st usart_comm;
usart_cfg_st *usart1_cfg_st;

extern st_rtdata_t rtdata;

void lowLevelInit(void);

// static functions
static void initPeripherialStructures(void);
static void init(void);
static void exec1(void);

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

// --------------------------------------------------------------------------
void lowLevelInit(void)
{
    initIo();
}

// static functions
// initialize peripherial structures
// --------------------------------------------------------------------------
static void initPeripherialStructures(void)
{
    // USART for PC communication
    memset(&usart_comm, 0, sizeof(usart_comm));
    usart_comm.usart_if = (uint32_t)USART_COMM_IF;
    usart_comm.usart_rcc = USART_COMM_RCC;
    usart_comm.usart_afio_rcc = USART_COMM_AFIO_RCC;
    usart_comm.usart_gpio.gpio = (uint32_t)USART_COMM_GPIO;
    usart_comm.usart_gpio.gpio_rcc = USART_COMM_GPIO_RCC;
    usart_comm.usart_rx_pin = USART_COMM_RX;
    usart_comm.usart_tx_pin = USART_COMM_TX;
    usart_comm.usart_irq = USART_COMM_IRQ;

    usart1_cfg_st = &usart_comm;
}

// --------------------------------------------------------------------------
static void init(void)
{
    initPeripherialStructures();
    usartInit(&usart_comm, USART_COMM_BAUDRATE, false, USART_PARITY_NONE);
    syncTimerInit();
}

// --------------------------------------------------------------------------
static void exec1(void)
{
    if (GPIO_ReadOutputDataBit(LED_GPIO, LED_PIN))
            GPIO_ResetBits(LED_GPIO, LED_PIN);
    else
            GPIO_SetBits(LED_GPIO, LED_PIN);
}

// END
