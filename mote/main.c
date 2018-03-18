/*
 *
 */

#include <string.h>

#ifndef MY_BOARD_ID
#define MY_BOARD_ID (0)
#endif /* MY_BOARD_ID */

#include "periph_cpu.h"
#include "fmt.h"
#include "uart_stdio.h"

#include "board.h"

#include "net/loramac.h"
#include "semtech_loramac.h"

#define LED_GREEN_ON     LED1_ON
#define LED_GREEN_OFF    LED1_OFF
#define LED_GREEN_TOGGLE LED1_TOGGLE

#define LED_BLUE_ON      LED2_ON
#define LED_BLUE_OFF     LED2_OFF
#define LED_BLUE_TOGGLE  LED2_TOGGLE

#define LED_RED_ON       LED3_ON
#define LED_RED_OFF      LED3_OFF
#define LED_RED_TOGGLE   LED3_TOGGLE

semtech_loramac_t loramac;


//#define MY_DR LORAMAC_DR_1
#define MY_DR LORAMAC_DR_5

//static const uint8_t deveui[LORAMAC_DEVEUI_LEN] = ...;
//static uint8_t appeui[LORAMAC_APPEUI_LEN] = ...;
//static uint8_t appkey[LORAMAC_APPKEY_LEN] = ...;
#include "lorawan-keys.c-inc"

#define LINE_BUFFER 512
uint8_t line[LINE_BUFFER+1];
size_t line_pos = 0;
char message [LINE_BUFFER/2];
size_t message_size;

int get_line(void)
{
    line_pos = 0;
    while (1) {
        int count = uart_stdio_read(((char*)line)+line_pos,
                                    LINE_BUFFER-line_pos);
        if (count < 0) {
            printf("Error: line.\n");
            continue;
        }
        line_pos += count;
        for (unsigned int i=0;i<line_pos;i++) {
            if (line[i] == '\n')
                return i;
        }
    }
}

int main(void)
{
#if 0    
    uint8_t my_cpuid[CPUID_LEN];
    cpuid_get(my_cpuid);
    printf("+ cpuid=");
    for (size_t i=0; i<CPUID_LEN; i++)
        fmt_hex_bytes(my_cpuid[i]);
    printf("\n");
#endif
    printf("@@BOOT %u\n", MY_BOARD_ID);
    
    uart_stdio_init();

    /*--- setup loramac interface */

    LED_BLUE_ON;
    
    /* 2. initialize the LoRaMAC MAC layer */
    //printf("+ LoRaMAC init\n");
    semtech_loramac_set_dr(&loramac, MY_DR);
    xtimer_sleep(1);
    semtech_loramac_init(&loramac);
    xtimer_sleep(1);    
    semtech_loramac_set_dr(&loramac, MY_DR);    
    /* 3. set the device required keys */
    if (MY_BOARD_ID == 0) {
        semtech_loramac_set_deveui(&loramac, deveui);
        semtech_loramac_set_appeui(&loramac, appeui);
        semtech_loramac_set_appkey(&loramac, appkey);
    }
    else if (MY_BOARD_ID == 10) {
        semtech_loramac_set_deveui(&loramac, deveui);
        appkey[0] = 0;
        semtech_loramac_set_appeui(&loramac, appeui);
        semtech_loramac_set_appkey(&loramac, appkey);
    }
    else if (MY_BOARD_ID == 1) {        
        semtech_loramac_set_deveui(&loramac, deveui2);
        semtech_loramac_set_appeui(&loramac, appeui2);
        semtech_loramac_set_appkey(&loramac, appkey2);        
    }
    else if (MY_BOARD_ID == 11) {        
        semtech_loramac_set_deveui(&loramac, deveui2);
        appkey2[0] = 0;        
        semtech_loramac_set_appeui(&loramac, appeui2);
        semtech_loramac_set_appkey(&loramac, appkey2);        
    }

    /*--- start the OTAA join procedure */

    if (semtech_loramac_join(&loramac, LORAMAC_JOIN_OTAA)
	!= SEMTECH_LORAMAC_JOIN_SUCCEEDED) {
      LED_BLUE_OFF;
      LED_RED_ON;
      puts("@@JOIN FAILURE\n");
      return -1;
    }
    puts("@@JOIN SUCCESS\n");
    LED_BLUE_OFF;
    LED_GREEN_ON;

    /*--- wait 1 second in case of join success, and set DR5, and wait */
    xtimer_sleep(1);

    semtech_loramac_set_adr(&loramac, false);
    semtech_loramac_set_dr(&loramac, MY_DR);

    xtimer_sleep(1);

    /*--- main measurement loop */
    
    //int i = 1;
    while (1) {

        int line_size = 0;
        while (1) {
            printf("@@READ\n");
            line_size = get_line();
            line[line_size] = '\0';
            message_size = fmt_hex_bytes((uint8_t*)message, (char*)line);
            printf("line (#%d -> %d) = %s\n", line_size, message_size, line);
            if (line_size == 0 || message_size > 0)
                break;
        }
        
        /* for received packets */
        semtech_loramac_rx_data_t rx_data;
        
	LED_BLUE_ON;
	printf("@@SENDING\n");
        loramac.port = 2;
        loramac.cnf = LORAMAC_TX_UNCNF;
        //loramac.cnf = LORAMAC_TX_CNF;
        //semtech_loramac_set_dr(&loramac, LORAMAC_DR_5);        
        uint8_t status = semtech_loramac_send
            (&loramac, (uint8_t *)message, message_size);
	printf("@@SENT %u\n", status);
	if (status == SEMTECH_LORAMAC_RX_DATA) {
	    unsigned int l = rx_data.payload_len;
	    if (l >= sizeof(rx_data.payload))
	        l = sizeof(rx_data.payload);
            printf("@@WRITE\n");
            for (size_t i=0; i<l; i++) { 
                print_byte_hex(rx_data.payload[l]);
            }
            printf("\n");
	}
	LED_BLUE_OFF;

        /* wait 5,10,15,... seconds between each message */
        //xtimer_sleep(i*5);
#if 0        
	if (i<20)
	    i ++;
#endif
    }

    return 0; /* should never be reached */
}
