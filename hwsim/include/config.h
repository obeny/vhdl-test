#ifndef _CONFIG_H
#define _CONFIG_H

#include "global.h"
#include "platform_config.h"

// SYNC TIMER
#define SYNC_TIMER_MAINTAIN_PERIOD
#define SYNC_TIMER_TIMERS 1
#define SYNC_TIMER_1000MS 0
#define SYNC_TIMER_1000MS_VAL 1000

// USART
#define USART_RBUF_SIZE 256
#define USART_TBUF_SIZE 256
#define USART_SEND_MAX_LENGTH 256
#define USART_BIG_BUFFERS

#define USART_COMM_BAUDRATE 1152

#endif // _CONFIG_H
