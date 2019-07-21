#include "stm32f10x.h"

#include "gpio.h"

pin_data_t pin_data[GPIO_CNT] = 
{
    // pins used: a15,b3,b4 = jtag, a9,a10 = uart
    // GPIOA
    {.port = GPIOA, .pin = GPIO_Pin_0},
    {.port = GPIOA, .pin = GPIO_Pin_1},
    {.port = GPIOA, .pin = GPIO_Pin_2},
    {.port = GPIOA, .pin = GPIO_Pin_3},
    {.port = GPIOA, .pin = GPIO_Pin_4},
    {.port = GPIOA, .pin = GPIO_Pin_5},
    {.port = GPIOA, .pin = GPIO_Pin_6},
    {.port = GPIOA, .pin = GPIO_Pin_7},
    {.port = GPIOA, .pin = GPIO_Pin_8},
    {.port = GPIOA, .pin = GPIO_Pin_11},
    {.port = GPIOA, .pin = GPIO_Pin_12},
    // GPIOB
    {.port = GPIOB, .pin = GPIO_Pin_0},
    {.port = GPIOB, .pin = GPIO_Pin_1},
    {.port = GPIOB, .pin = GPIO_Pin_5},
    {.port = GPIOB, .pin = GPIO_Pin_6},
    {.port = GPIOB, .pin = GPIO_Pin_7},
    {.port = GPIOB, .pin = GPIO_Pin_8},
    {.port = GPIOB, .pin = GPIO_Pin_9},
    {.port = GPIOB, .pin = GPIO_Pin_10},
    {.port = GPIOB, .pin = GPIO_Pin_11},
    {.port = GPIOB, .pin = GPIO_Pin_12},
    {.port = GPIOB, .pin = GPIO_Pin_13},
    {.port = GPIOB, .pin = GPIO_Pin_14},
    {.port = GPIOB, .pin = GPIO_Pin_15}
};

// static functions
static void ioPinDir(GPIO_TypeDef* gpio, UINT16 pin_pos, GPIOMode_TypeDef mode);

// --------------------------------------------------------------------------
static void ioPinDir(GPIO_TypeDef* gpio, UINT16 pin_pos, GPIOMode_TypeDef mode)
{
    GPIO_InitTypeDef pin;

    pin.GPIO_Pin = pin_pos;
    pin.GPIO_Speed = GPIO_Speed_50MHz;
    pin.GPIO_Mode = mode;

    GPIO_Init(gpio, &pin);
}

// --------------------------------------------------------------------------
void resetIo(void)
{
    for (UINT8 pin = 0; pin < GPIO_CNT; ++pin)
        ioPinDir(pin_data[pin].port, pin_data[pin].pin, GPIO_Mode_IN_FLOATING);
}

// --------------------------------------------------------------------------
void setPinDir(UINT8 gpio, e_pindir_t dir)
{
    GPIOMode_TypeDef pindir = GPIO_Mode_IN_FLOATING;
    if (E_PINDIR_OUT == dir)
        pindir = GPIO_Mode_Out_PP;

    ioPinDir(pin_data[gpio].port, pin_data[gpio].pin, pindir);
}

// --------------------------------------------------------------------------
void setPinValue(UINT8 gpio, BOOL value)
{
    GPIO_WriteBit(pin_data[gpio].port, pin_data[gpio].pin, value);
}

// --------------------------------------------------------------------------
bool getPinValue(UINT8 gpio)
{
    return (GPIO_ReadInputDataBit(pin_data[gpio].port, pin_data[gpio].pin));
}
