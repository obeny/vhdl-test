#ifndef PLATFORM_H
#define PLATFORM_H

#include "global.h"

#include "stm32f10x.h"
#include "stm32f10x_gpio.h"

#define STACK_SIZE 0x100
#define STACK_CHECK_THRSH 32

#define GPIO_CNT 24

#define MAX_SIGNALS (GPIO_CNT+1)
#define MAX_VECTORS (UINT8_MAX)
#define MAX_TESTCASES 32

typedef GPIO_TypeDef* port_t;
typedef UINT16 pin_t;

#endif // PLATFORM_H
