/***************************************************************************
 *      INCLUDES
 ***************************************************************************/

#include "stm32f10x_gpio.h"
#include "stm32f10x_rcc.h"

#include "config.h"
#include "io.h"

#include "gpio.h"


/***************************************************************************
 *      FUNCTIONS
 ***************************************************************************/


// --------------------------------------------------------------------------
void initIo(void)
{
    GPIO_InitTypeDef pin;

    // clocks
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);

    // LED
    pin.GPIO_Pin = LED_PIN;
    pin.GPIO_Speed = GPIO_Speed_10MHz;
    pin.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_Init(LED_GPIO, &pin);
    GPIO_ResetBits(LED_GPIO, LED_PIN);

    // sim GPIOs
    resetIo();
}

// END
