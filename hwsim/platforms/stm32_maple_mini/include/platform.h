#ifndef PLATFORM_H
#define PLATFORM_H

#include "global.h"

#include "stm32f10x.h"
#include "stm32f10x_gpio.h"

#define STACK_SIZE 0x100
#define STACK_CHECK_THRSH 32

#define GPIO_CNT 24

#define TC_NAME_LEN 32
#define MAX_SIGNALS 64
#define MAX_VECTORS (UINT8_MAX)
#define MAX_TESTCASES 24

typedef GPIO_TypeDef* port_t;
typedef UINT16 pin_t;

enum
{
    E_SIGVAL_DC = '-',
    E_SIGVAL_SET_L = '0',
    E_SIGVAL_SET_H = '1',
    E_SIGVAL_EXP_L = 'l',
    E_SIGVAL_EXP_H = 'h'
} e_sig_val;

#endif // PLATFORM_H
