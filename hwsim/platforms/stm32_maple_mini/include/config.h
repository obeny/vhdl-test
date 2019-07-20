#ifndef _CONFIG_H
#define _CONFIG_H

#include "global.h"
#include "stm32f10x_gpio.h"
#include "stm32f10x_rcc.h"
#include "stm32f10x.h"

// CPU frequency
#define XTAL_FREQ 8000000UL
#define INTOSC_FREQ 8000000UL

#define MCK_USE_PLL
// #define MCK_USE_XTAL
// #define MCK_USE_INTOSC

#define PLL_MUL 9
#define PLL_RCC_MUL RCC_PLLMul_9

#define PLL_DIV 1
#define PLL_RCC_DIV RCC_PLLSource_HSE_Div1

#if (defined MCK_USE_INTOSC)
#define F_CPU INTOSC_FREQ
#elif (defined MCK_USE_XTAL)
#define F_CPU XTAL_FREQ
#elif (defined MCK_USE_PLL)
#define F_CPU (XTAL_FREQ * PLL_MUL / PLL_DIV)
#endif

// MISC
#define LOWLEVELINIT

// IO
#define LED_GPIO GPIOC
#define LED_PIN GPIO_Pin_13

// SYNC TIMER
#define SYNC_TIMER_MAINTAIN_PERIOD
#define SYNC_TIMER_TIMERS 1
#define SYNC_TIMER_1000MS 0
#define SYNC_TIMER_1000MS_VAL 1000

// USART
#define USART_RBUF_SIZE 256
#define USART_TBUF_SIZE 256
#define USART_SEND_MAX_LENGTH 256
#define USART_USE1
#define USART_BIG_BUFFERS

// USART1 - communication
#define USART_COMM_IF USART1
#define USART_COMM_RCC RCC_APB2Periph_USART1
#define USART_COMM_AFIO_RCC RCC_APB2Periph_AFIO

#define USART_COMM_GPIO GPIOA
#define USART_COMM_GPIO_RCC RCC_APB2Periph_GPIOA

#define USART_COMM_BAUDRATE 1152
#define USART_COMM_RX 10
#define USART_COMM_TX 9

#define USART_COMM_IRQ USART1_IRQn;

#endif // _CONFIG_H
