#ifndef DILDER_BT_H
#define DILDER_BT_H
#include <stdbool.h>
#include <stdint.h>

/* BT_PAIRING = a 6-digit passkey is on screen, waiting for the phone to enter it. */
typedef enum { BT_OFF, BT_STARTING, BT_ADVERTISING, BT_CONNECTED, BT_PAIRING, BT_PAIRED } bt_state_t;

void        dilder_bt_init(void);    /* one-time: HCI/GATT/SM setup + power on + advertise */
void        dilder_bt_stop(void);    /* stop advertising + power off */
bt_state_t  dilder_bt_state(void);
const char *dilder_bt_peer(void);    /* connected peer address, "" if none */
bool        dilder_bt_active(void);  /* true once init'd — poll cyw43 while active */
uint32_t    dilder_bt_passkey(void); /* 6-digit pairing code to show, 0 if none */

/* Custom GATT service bridge to the app. */
void        dilder_bt_set_status(const char *s); /* phone-readable "MOOD STEPS"; notifies subscribers */
int         dilder_bt_take_command(void);        /* byte the phone last wrote, or -1; clears it */

#endif
