#ifndef GPIO_H
#define GPIO_H

#include "global.h"
#include "platform.h"

typedef struct
{
    port_t port;
    pin_t pin;
} pin_data_t;

typedef enum
{
    E_PINDIR_IN = 0,
    E_PINDIR_OUT = 1
} e_pindir_t;

void resetIo(void);

void setPinDir(UINT8 gpio, e_pindir_t dir);
void setPinValue(UINT8 gpio, BOOL value);
bool getPinValue(UINT8 gpio);

void tickClock(UINT8 gpio);

#endif // GPIO_H
