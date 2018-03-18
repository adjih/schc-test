# name of the application
APPLICATION = lora-device

# The default board is ST B-L072Z-LRWAN1 LoRa discovery board
BOARD ?= b-l072z-lrwan1

# The RIOT source code is in ~/RIOT
RIOTBASE ?= $(CURDIR)/../../RIOT

#
# Here we add the modules that are needed
#
USEMODULE += xtimer

#
# The application needs LoRaWAN related modules and variables:
#

# The Semtech LoRa radio device (SX1276)
USEMODULE += sx1276

#USEMODULE += hts221
USEMODULE += fmt

# The Semtech Loramac package
USEPKG += semtech-loramac

# Because of the regional parameters, we also need to define the region
CFLAGS += -DREGION_EU868

MY_BOARD_ID ?= 0
CFLAGS += -DMY_BOARD_ID=${MY_BOARD_ID}

include $(RIOTBASE)/Makefile.include
