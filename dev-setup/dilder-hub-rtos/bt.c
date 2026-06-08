/* Dilder Hub — BLE peripheral: advertise as "Dilder Hub", accept a connection
 * from a phone, pair/bond with a passkey shown on screen, and expose a small
 * custom GATT service (read live status + notify, write a command byte). */
#include "bt.h"
#include <stdio.h>
#include <string.h>
#include "btstack.h"
#include "dilder.h"   /* generated from dilder.gatt by pico_btstack_make_gatt_header */

/* Handle macros from the generated GATT header (custom 0xFFE0 service). */
#define H_STATUS_VALUE  ATT_CHARACTERISTIC_0000FFE1_0000_1000_8000_00805F9B34FB_01_VALUE_HANDLE
#define H_STATUS_CCC    ATT_CHARACTERISTIC_0000FFE1_0000_1000_8000_00805F9B34FB_01_CLIENT_CONFIGURATION_HANDLE
#define H_CMD_VALUE     ATT_CHARACTERISTIC_0000FFE2_0000_1000_8000_00805F9B34FB_01_VALUE_HANDLE

static bt_state_t g_state  = BT_OFF;
static bool       g_active = false;
static char       g_peer[20] = "";
static uint32_t   g_passkey = 0;
static btstack_packet_callback_registration_t hci_reg, sm_reg;

static char            g_status[24] = "BOOTING 0";
static int             g_cmd        = -1;
static hci_con_handle_t g_con       = HCI_CON_HANDLE_INVALID;
static bool            g_notify     = false;
static btstack_context_callback_registration_t g_notify_cb;

/* Advertising payload: general-discoverable flags + complete local name. */
static const uint8_t adv_data[] = {
    0x02, BLUETOOTH_DATA_TYPE_FLAGS, 0x06,
    0x0B, BLUETOOTH_DATA_TYPE_COMPLETE_LOCAL_NAME,
    'D', 'i', 'l', 'd', 'e', 'r', ' ', 'H', 'u', 'b',
};

static void start_advertising(void) {
    uint16_t adv_int_min = 0x0030, adv_int_max = 0x0030;
    bd_addr_t null_addr; memset(null_addr, 0, sizeof(null_addr));
    gap_advertisements_set_params(adv_int_min, adv_int_max, 0, 0, null_addr, 0x07, 0x00);
    gap_advertisements_set_data(sizeof(adv_data), (uint8_t *)adv_data);
    gap_advertisements_enable(1);
    g_state = BT_ADVERTISING;
}

/* ── Custom GATT service: read status, write command, notify on change ── */
static uint16_t att_read_cb(hci_con_handle_t con, uint16_t handle, uint16_t offset,
                            uint8_t *buf, uint16_t buf_size) {
    (void)con;
    if (handle == H_STATUS_VALUE)
        return att_read_callback_handle_blob((const uint8_t *)g_status,
                                             (uint16_t)strlen(g_status), offset, buf, buf_size);
    return 0;
}

static int att_write_cb(hci_con_handle_t con, uint16_t handle, uint16_t mode,
                        uint16_t offset, uint8_t *buf, uint16_t buf_size) {
    (void)con; (void)mode; (void)offset;
    if (handle == H_CMD_VALUE) {
        if (buf_size > 0) g_cmd = buf[0];
    } else if (handle == H_STATUS_CCC) {
        g_notify = (buf_size >= 2) && (little_endian_read_16(buf, 0) != 0);
    }
    return 0;
}

static void notify_now(void *ctx) {
    (void)ctx;
    if (g_con != HCI_CON_HANDLE_INVALID && g_notify)
        att_server_notify(g_con, H_STATUS_VALUE, (const uint8_t *)g_status, (uint16_t)strlen(g_status));
}

static void hci_handler(uint8_t type, uint16_t ch, uint8_t *packet, uint16_t size) {
    (void)ch; (void)size;
    if (type != HCI_EVENT_PACKET) return;
    switch (hci_event_packet_get_type(packet)) {
        case BTSTACK_EVENT_STATE:
            if (btstack_event_state_get_state(packet) == HCI_STATE_WORKING) start_advertising();
            break;
        case HCI_EVENT_DISCONNECTION_COMPLETE:
            g_peer[0] = '\0';
            g_passkey = 0;
            g_con     = HCI_CON_HANDLE_INVALID;
            g_notify  = false;
            start_advertising();
            break;
        case HCI_EVENT_LE_META:
            if (hci_event_le_meta_get_subevent_code(packet) == HCI_SUBEVENT_LE_CONNECTION_COMPLETE) {
                bd_addr_t addr;
                hci_subevent_le_connection_complete_get_peer_address(packet, addr);
                snprintf(g_peer, sizeof(g_peer), "%s", bd_addr_to_str(addr));
                g_con   = hci_subevent_le_connection_complete_get_connection_handle(packet);
                g_state = BT_CONNECTED;
            }
            break;
        default:
            break;
    }
}

static void sm_handler(uint8_t type, uint16_t ch, uint8_t *packet, uint16_t size) {
    (void)ch; (void)size;
    if (type != HCI_EVENT_PACKET) return;
    switch (hci_event_packet_get_type(packet)) {
        case SM_EVENT_PASSKEY_DISPLAY_NUMBER:
            g_passkey = sm_event_passkey_display_number_get_passkey(packet);
            g_state   = BT_PAIRING;
            break;
        case SM_EVENT_PAIRING_COMPLETE:
            g_passkey = 0;
            if (sm_event_pairing_complete_get_status(packet) == ERROR_CODE_SUCCESS) g_state = BT_PAIRED;
            else g_state = BT_CONNECTED;
            break;
        case SM_EVENT_REENCRYPTION_COMPLETE:
            g_state = BT_PAIRED;
            break;
        default:
            break;
    }
}

void dilder_bt_init(void) {
    if (g_active) return;
    g_active = true;
    g_state  = BT_STARTING;

    l2cap_init();
    sm_init();
    /* DISPLAY_ONLY → device shows a passkey, phone enters it (Passkey Entry). */
    sm_set_io_capabilities(IO_CAPABILITY_DISPLAY_ONLY);
    sm_set_authentication_requirements(SM_AUTHREQ_MITM_PROTECTION | SM_AUTHREQ_BONDING | SM_AUTHREQ_SECURE_CONNECTION);

    att_server_init(profile_data, att_read_cb, att_write_cb);

    hci_reg.callback = &hci_handler;
    hci_add_event_handler(&hci_reg);
    att_server_register_packet_handler(hci_handler);
    sm_reg.callback = &sm_handler;
    sm_add_event_handler(&sm_reg);

    g_notify_cb.callback = &notify_now;
    hci_power_control(HCI_POWER_ON);
}

void dilder_bt_stop(void) {
    if (!g_active) return;
    gap_advertisements_enable(0);
    hci_power_control(HCI_POWER_OFF);
    g_active  = false;
    g_state   = BT_OFF;
    g_con     = HCI_CON_HANDLE_INVALID;
    g_notify  = false;
    g_passkey = 0;
}

void dilder_bt_set_status(const char *s) {
    if (!s) return;
    if (strncmp(g_status, s, sizeof(g_status)) == 0) return;   /* unchanged → no notify */
    snprintf(g_status, sizeof(g_status), "%s", s);
    if (g_con != HCI_CON_HANDLE_INVALID && g_notify) {
        g_notify_cb.context = NULL;
        att_server_request_to_send_notification(&g_notify_cb, g_con);
    }
}

int dilder_bt_take_command(void) {
    int c = g_cmd;
    g_cmd = -1;
    return c;
}

bt_state_t  dilder_bt_state(void)   { return g_state; }
const char *dilder_bt_peer(void)    { return g_peer; }
bool        dilder_bt_active(void)  { return g_active; }
uint32_t    dilder_bt_passkey(void) { return g_passkey; }
