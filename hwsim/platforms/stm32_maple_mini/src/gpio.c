#include "stm32f10x.h"

#include "gpio.h"

pin_data_t pin_data[GPIO_CNT] = 
{
    // pins used: a15,b3,b4 = jtag, a9,a10 = uart
    // GPIOA
    {.port = GPIOA, .pin = 0},
    {.port = GPIOA, .pin = 1},
    {.port = GPIOA, .pin = 2},
    {.port = GPIOA, .pin = 3},
    {.port = GPIOA, .pin = 4},
    {.port = GPIOA, .pin = 5},
    {.port = GPIOA, .pin = 6},
    {.port = GPIOA, .pin = 7},
    {.port = GPIOA, .pin = 8},
    {.port = GPIOA, .pin = 11},
    {.port = GPIOA, .pin = 12},
    // GPIOB
    {.port = GPIOB, .pin = 0},
    {.port = GPIOB, .pin = 1},
    {.port = GPIOB, .pin = 5},
    {.port = GPIOB, .pin = 6},
    {.port = GPIOB, .pin = 7},
    {.port = GPIOB, .pin = 8},
    {.port = GPIOB, .pin = 9},
    {.port = GPIOB, .pin = 10},
    {.port = GPIOB, .pin = 11},
    {.port = GPIOB, .pin = 12},
    {.port = GPIOB, .pin = 13},
    {.port = GPIOB, .pin = 14},
    {.port = GPIOB, .pin = 15}
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
