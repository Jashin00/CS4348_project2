# CS4348 Project 2

## Overview
This project simulates a bank using threads and semaphores in Python.

There are:
- 3 teller threads
- 50 customer threads

The program models the following bank rules:
- The bank opens only after all 3 tellers are ready
- Only 2 customers can enter through the door at the same time
- If a teller is free, a customer selects that teller
- Only 1 teller can talk to the manager at a time
- Only 2 tellers can use the safe at a time
- Withdrawals require manager approval before going to the safe
- The bank closes after all customers have been served

## Files
- `project2.py`  
  Main Python source file for the bank simulation.  
  It contains:
  - the `Teller` thread class
  - the `Customer` thread class
  - semaphore synchronization logic
  - the main function that starts and stops the simulation

- `README.md`  
  This file. It explains the program structure and how to run it.

## How to Run
Make sure you have Python 3 installed.

Run the program from the command line with:

```bash
python3 bank.py

```
If your system uses python for Python 3, you can also run:
```bash
python bank.py
```