/***************************************************************************
 *      INCLUDES
 ***************************************************************************/

#include "config.h"

#include "io.h"
#include "usart.h"

#include "stm32f10x_gpio.h"

#include <string.h>


/***************************************************************************
 *      DEFINITIONS
 ***************************************************************************/

extern usart_cfg_st usart_comm;
usart_cfg_st *usart1_cfg_st;

void lowLevelInit(void);
void initPeripherialStructures(void);
void exec1(void);


 /***************************************************************************
 *      FUNCTIONS
 ***************************************************************************/

// --------------------------------------------------------------------------
void lowLevelInit(void)
{
    initIo();
}

// initialize peripherial structures
// --------------------------------------------------------------------------
void initPeripherialStructures(void)
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

// blink led to indicate activity
// --------------------------------------------------------------------------
void exec1(void)
{
    if (GPIO_ReadOutputDataBit(LED_GPIO, LED_PIN))
            GPIO_ResetBits(LED_GPIO, LED_PIN);
    else
            GPIO_SetBits(LED_GPIO, LED_PIN);
}

// END
