# Development Log - CS 4348 Project 2

## Date and time: 4:00PM 4/17/2026
Session 1

In this session, I started by reading through the full Project 2 description and figuring out what the program actually needs to simulate. The project is a bank with 3 tellers and 50 customers, where customers either deposit or withdraw, tellers may need to use the manager for withdrawals, and only two tellers can use the safe at the same time.

My main goal for this session was to break the assignment into parts before writing code. I identified the important shared resources and synchronization points: the bank opening condition, the customer line, teller availability, the door that allows only two customers at a time, the manager, and the safe. I also outlined the sequence of actions for both teller threads and customer threads so I would know exactly what each thread needs to do. The project requires Python threads and semaphores if using Python, so I planned to use the threading module and threading.Semaphore.

