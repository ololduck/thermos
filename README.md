# Thermos

This is *Thermos* (\tɛʁ.mɔs\\), a simple, DIY thermostat solution for home hobbyists, based on the RaspberryPI minimal computer.

It is relatively cheap, since if you already own soldering equipment, it comes to less than 40€, which is 60€ less than most basic thermostat units found in retail.

I wanted to install a thermostat to save on heating in the winter of 2018, but was rebuked by the price of commercial solutions.

## Hardware:

- A 220AC->5vDC 5W power supply
- A RaspberryPi computer, I use the model zero, since it is cheap, has more than enough computing power, and is capable of networking.
- A relay board, to open or close the heater's control circuit
- A 1wire enabled temperature probe, such as the DS18b20, which will report current temperature
- A bit of PCB to hold all of this together

## Python-based daemon

At its core, a python daemon checks the temperature probe, and updates a relay to close (or open) a control circuit, linked to your home heater.

The choice of python is motivated by the fact that this is still an early stage of development, and I wanted to iterate quickly on a simple idea. My goal is to write the "final" version in a language closer to the machine, such as [rust](https://rustlang.org) or [go](https://golang.org). That would lower the CPU consumption, and as such would enable lower overall electrical consumption.


## Features wishlist

- Weekly schedules
- Hourly schedules - Done!
- Configuration client(s?)
  - web-based
  - Android?
- Reporting as graphs and whatever
- Heating predictions (if my schedule says i must be at 18°C, start heating to have 18°C at specified hour)
- Multiple temperature probes
- Energy savings reporting

## Content of this repository

My aim with this repository is to centralize all information on this project. That means the code, the PCB design files, documentation... and so on. Someone should be able to build one following simple steps.

## Final words

Happy reading & hacking!
