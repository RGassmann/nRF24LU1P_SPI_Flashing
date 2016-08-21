#!/usr/bin/env python3

# This script should work on any Raspberry pi running a recent version of
# rasbian. After the Crazyradio is connected to the raspberry pi expansion
# port just run the script with "python3 fix_bootloader_raspi.py"
# See readme for more information about this script purpose.

# Script setup. Use this as a documentation to cable the Crazyradio or modify
# if you want to cable it differently.
# Name   Pin on raspi     Pin on Crazyradio
#-------------------------------------------
GND   =   6              # 9
RESET =   18             # 3
PROG  =   22             # 2
SCK   =   23             # 4
MOSI  =   19             # 6
MISO  =   21             # 8
CS    =   24             # 10

import RPi.GPIO as GPIO
import time
import sys

CS_ENABLE = GPIO.LOW
CS_DISABLE = GPIO.HIGH

# SPI commands
WREN = 0x06
WRDIS = 0x04
RDSR = 0x05
WRSR = 0x01
ERASE_PAGE = 0x52
ERASE_ALL = 0x62
PROGRAM = 0x02
READ = 0x03
RDFPCR = 0x89
RDISMB = 0x85
ENDEBUG = 0x86
RDYN = 0x10

FSR_RDYN = 0x10
FSR_WEN = 0x20
FSR_INFEN = 0x08

CHIP_ID = [0] * 5

#CHIP_ID = [0xc1, 0x0e, 0x75, 0xD4,0x8A]


def init_gpios():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(RESET, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PROG, GPIO.OUT, initial=GPIO.HIGH)


def check_connection():
    # If reset is connected, it will be pulled up
    return GPIO.input(RESET) != 0


def reset_in_prog():
    GPIO.output(RESET, GPIO.LOW)
    GPIO.output(PROG, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(RESET, GPIO.HIGH)
    time.sleep(0.1)


def reset_in_fw():
    GPIO.output(RESET, GPIO.LOW)
    GPIO.output(PROG, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(RESET, GPIO.HIGH)
    time.sleep(0.1)


def spi_oe(enable):
    if enable:
        GPIO.setup(MOSI, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(SCK, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(CS, GPIO.OUT, initial=CS_DISABLE)
        GPIO.setup(MISO, GPIO.IN)
    else:
        GPIO.setup(SCK , GPIO.IN)
        GPIO.setup(MOSI, GPIO.IN)
        GPIO.setup(CS  , GPIO.IN)


def set_cs(value):
    GPIO.output(CS, value)
    time.sleep(0.1)


def spi_transfer(dataout):
    datain = 0
    GPIO.output(SCK, GPIO.LOW)
    for i in range(8):
        b = GPIO.LOW
        if dataout & 0x0080 != 0:
            b = GPIO.HIGH
        GPIO.output(MOSI, b)
        dataout = dataout << 1

        time.sleep(0.001)
        b = GPIO.input(MISO)
        GPIO.output(SCK, GPIO.HIGH)

        datain = datain << 1
        if b != GPIO.LOW:
            datain = datain | 0x01

        time.sleep(0.001)
        GPIO.output(SCK, GPIO.LOW)

    return datain

def select_MainBlock():
    print("Selecting Mainblock...")
    set_cs(CS_ENABLE)
    spi_transfer(WRSR)
    spi_transfer(0)
    set_cs(CS_DISABLE)

def select_Info_Page():
    print("Selecting Infopage...")
    set_cs(CS_ENABLE)
    spi_transfer(WRSR)
    spi_transfer(FSR_INFEN)
    set_cs(CS_DISABLE)

def write_CHIPID():
    print("Writing Chip-ID...")
    set_cs(CS_ENABLE)
    spi_transfer(PROGRAM)
    spi_transfer(0x00)
    spi_transfer(0x0B)
    for num in range(5):
        spi_transfer(CHIP_ID[num])
    set_cs(CS_DISABLE)

def verify_CHIPID():
    print("Verify Chip-ID: ", end="")
    set_cs(CS_ENABLE)
    spi_transfer(READ)
    spi_transfer(0x00)
    spi_transfer(0x0B)
    verify = True
    for num in range(5):
        if CHIP_ID[num] != spi_transfer(0x00):
            verify = false
    if verify :
        print("Verify OK");
    else :
        print("Verify FAILED")
    set_cs(CS_DISABLE)

def read_CHIPID():
    print("Reading Chip-ID: ", end="")
    set_cs(CS_ENABLE)
    spi_transfer(READ)
    spi_transfer(0x00)
    spi_transfer(0x0B)
    print("Chip-ID is: ", end="")
    for num in range(5):
        CHIP_ID[num] = spi_transfer(0x00)
        print("{:02x}".format(CHIP_ID[num]), end=" ")
    print("");
    set_cs(CS_DISABLE)

def read_InfoPage():
    print("Reading Infopage: ", end="")
    set_cs(CS_ENABLE)
    spi_transfer(READ)
    spi_transfer(0x00)
    spi_transfer(0x20)
    print("Infopage is: ", end="")
    print("{:02x}".format(spi_transfer(0x00)), end=" ")
    print("{:02x}".format(spi_transfer(0x00)), end=" ")
    print("{:02x}".format(spi_transfer(0x00)), end=" ")
    print("{:02x}".format(spi_transfer(0x00)), end=" ")
    print("{:02x}".format(spi_transfer(0x00)))
    set_cs(CS_DISABLE)

def read_MainBlock():
    print("Reading Mainblock: ")
    set_cs(CS_ENABLE)
    spi_transfer(READ)
    spi_transfer(0x7F)
    spi_transfer(0x50)
    print("Should be:")
    print("Nordic Semiconductor.nRF24LU1P-F32 BOOT LDR")
    print("is:")
    for num in range(43):
        spi_transfer(0x00)
        print(chr(spi_transfer(0x00)), end="")
    print("");
    set_cs(CS_DISABLE)

def enable_Write():
    print("Enabling Write... ", end="")
    set_cs(CS_ENABLE)
    spi_transfer(WREN)
    set_cs(CS_DISABLE)

    set_cs(CS_ENABLE)
    spi_transfer(RDSR)
    if (spi_transfer(0x00) & FSR_WEN) :
        print("OK")
    else:
        print("Could not enable Writing! Check Connection! And try again")
        exit()
    set_cs(CS_DISABLE)

def erase_MainBlock():
    print("Erasing Mainblock", end="")
    set_cs(CS_ENABLE)
    spi_transfer(ERASE_ALL)
    set_cs(CS_DISABLE)

    set_cs(CS_ENABLE)
    spi_transfer(RDSR) #Read Status Register
    while ( spi_transfer(0x00) & FSR_RDYN ):
        print('.', end="")
        spi_transfer(RDSR) #Read Status Register

    print(" Erased")
    set_cs(CS_DISABLE)

def erase_InfoPage():
    print("Erasing Infopage", end="")
    set_cs(CS_ENABLE)
    spi_transfer(ERASE_PAGE)
    spi_transfer(0x00)
    set_cs(CS_DISABLE)

    set_cs(CS_ENABLE)
    spi_transfer(RDSR) #Read Status Register
    while ( spi_transfer(0x00) & FSR_RDYN ):
        print('.', end="")
        spi_transfer(RDSR) #Read Status Register

    print(" Erased")
    set_cs(CS_DISABLE)

def program_Device_FAST(): #Takes up to 1min
    print("Programming Device... (Just Boot LDR)")

    print("\nWait for Device Ready...")
    set_cs(CS_ENABLE)
    spi_transfer(RDSR) #Read Status Register
    while ( spi_transfer(0x00) & FSR_RDYN ):
        spi_transfer(RDSR) #Read Status Register
    set_cs(CS_DISABLE)
    enable_Write()
    print("Writing address: ", end ="")
    print("{:04x}".format(0))
    set_cs(CS_ENABLE)
    spi_transfer(PROGRAM)
    spi_transfer(0x00) #HiAdr
    spi_transfer(0x00) #LoAdr
    print("{:02x}".format(0x02), end=" ")
    spi_transfer(0x02)
    print("{:02x}".format(0x78), end=" ")
    spi_transfer(0x78)
    print("{:02x}".format(0x00), end=" ")
    spi_transfer(0x00)
    set_cs(CS_DISABLE)

    with open("/home/pi/Desktop/NRF/boot24lu1p-f32_padded.bin", "rb") as f:
        byte = f.read(1)
        num = 0
        adr = 0
        while adr < 0x7800:
            adr += 1
            byte= f.read(1)
        while byte:
            if ( (num % 250) == 0 ) :
                set_cs(CS_DISABLE)
                print("\nWait for Device Ready...")
                set_cs(CS_ENABLE)
                spi_transfer(RDSR) #Read Status Register
                while ( spi_transfer(0x00) & FSR_RDYN ):
                    #print('.', end="")
                    spi_transfer(RDSR) #Read Status Register
                set_cs(CS_DISABLE)
                enable_Write()
                print("Writing address: ", end ="")
                print("{:04x}".format(adr),end="")
                print(" of 7fff")
                set_cs(CS_ENABLE)
                spi_transfer(PROGRAM)
                spi_transfer((adr & 0xFF00)>>8)
                spi_transfer((adr & 0x00FF))
            print("{:02x}".format(ord(byte)), end=" ")
            spi_transfer(ord(byte))
            num += 1
            adr += 1
            byte= f.read(1)
        set_cs(CS_DISABLE)
        spi_transfer(RDSR) #Read Status Register
        while ( spi_transfer(0x00) & FSR_RDYN ):
            print('.', end="")
            spi_transfer(RDSR) #Read Status Register
        set_cs(CS_DISABLE)
    print("")
    print("Programming Finished...")


def program_Device_FULL(): #Takes up to 12min
    print("Programming Device... (Full Image)")
    with open("/home/pi/Desktop/NRF/boot24lu1p-f32_padded.bin", "rb") as f:
        byte = f.read(1)
        num = 0
        while byte:
            if ( (num % 250) == 0 ) :
                set_cs(CS_DISABLE)
                print("\nWait for Device Ready...")
                set_cs(CS_ENABLE)
                spi_transfer(RDSR) #Read Status Register
                while ( spi_transfer(0x00) & FSR_RDYN ):
                    #print('.', end="")
                    spi_transfer(RDSR) #Read Status Register
                set_cs(CS_DISABLE)
                enable_Write()
                print("Writing address: ", end ="")
                print("{:04x}".format(num),end="")
                print(" of 7fff")
                set_cs(CS_ENABLE)
                spi_transfer(PROGRAM)
                spi_transfer((num & 0xFF00)>>8)
                spi_transfer((num & 0x00FF))
            print("{:02x}".format(ord(byte)), end=" ")
            spi_transfer(ord(byte))
            num = num + 1;
            byte= f.read(1)
        set_cs(CS_DISABLE)
        spi_transfer(RDSR) #Read Status Register
        while ( spi_transfer(0x00) & FSR_RDYN ):
            print('.', end="")
            spi_transfer(RDSR) #Read Status Register
        set_cs(CS_DISABLE)
    print("Programming Finished...")

if __name__ == "__main__":
    print("nRF24LU1P-F32 Flasher (c) by Roman Gassmann")
    print("Programming the full image will take up to 12min!\nProgramming just the Boot LDR will take just 1min.")
    eingabe = 2
    while (eingabe != '0') and (eingabe != '1') :
        eingabe = input("Please enter\n1: Full image (12min)\n0: Just the Boot LDR (1min)\n")

    if eingabe == "0" :
        print("Programming just the BOOT LDR this takes up to 1min!")
    else :
        print("Programming the full Image takes up to 12min! Please be patient.")

    print(GPIO.VERSION)
    init_gpios()

    reset_in_prog()
    spi_oe(True)


    select_Info_Page()
    read_CHIPID()
    read_InfoPage()

    select_MainBlock()
    enable_Write()
    erase_MainBlock()

    select_Info_Page()
    enable_Write()
    erase_InfoPage()

    enable_Write()
    write_CHIPID()
    verify_CHIPID()

    select_MainBlock()
    enable_Write()
    if eingabe == "0" :
        program_Device_FAST()
    else :
        program_Device_FULL()


    select_MainBlock()
    read_MainBlock()

    spi_oe(False)

    reset_in_fw()

    GPIO.cleanup()