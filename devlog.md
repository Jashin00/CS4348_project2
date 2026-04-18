# Development Log - CS 4348 Project 2

## Date and time: 4:00 PM 4/17/2026
### Session 1: Understand the simulation and build the basic thread structure

In this session, I started by reading through the full Project 2 description and figuring out what the program actually needs to simulate. The project is a bank with 3 tellers and 50 customers, where customers either deposit or withdraw, tellers may need to use the manager for withdrawals, and only two tellers can use the safe at the same time.

My main goal for this session was to break the assignment into parts before writing code. I identified the important shared resources and synchronization points: the bank opening condition, the customer line, teller availability, the door that allows only two customers at a time, the manager, and the safe. I also outlined the sequence of actions for both teller threads and customer threads so I would know exactly what each thread needs to do. The project requires Python threads and semaphores if using Python, so I planned to use the `threading module` and `threading.Semaphore`.

By the end of this session, I had a clear plan for the structure of the program. I did not want to jump straight into all 50 customers because that would make debugging much harder. The next step is to build the basic teller and customer thread setup and get a simple interaction working first. I was able to create 3 tellers and 10 customers and print out the activities log of both but I was not too sure it is the right format for requirement of the project.

## Date and time: 5:05 PM 4/17/2026
### Session 2: Build synchronization between tellers and customers

I focused on coding the basic interaction between tellers and customers. I created the teller threads with unique IDs and customer threads with unique IDs, since the project says each thread should be distinguishable in the output.

After that, I worked on the synchronization between a teller and a customer. I wanted the first version to handle the essential interaction only: a customer enters, gets assigned to a ready teller, introduces itself, waits for the teller to ask for the transaction, gives the transaction, waits for completion, and then leaves. On the teller side, the teller announces readiness, waits for a customer, asks for the transaction, processes it, and then waits for the customer to leave before moving on. This matches the project sequence for both thread types.

I also started adding print statements in the required format so the program output would already be close to what the assignment expects. The required format is THREAD_TYPE ID [THREAD_TYPE ID]: MSG, so I planned the output around that from the beginning instead of fixing it later.

At the end of this session, I had the core handshake between customer and teller planned out and partially implemented. The next step is to add the constrained shared resources like the door, manager, and safe, then test the full flow with random delays.


## Date and time: 5:20 PM 4/17/2026
### Session 3: Add shared resources, timing, and full simulation
In this final session, I worked on the full simulation behavior and the resource restrictions that make the project more realistic. I added the semaphore logic for the door so that only two customers can enter at a time, for the safe so that only two tellers can be inside at once, and for the manager so that only one teller can interact with the manager at a time. The manager is only needed for withdrawals, so that condition also has to be checked in the teller logic.

I also added the random waiting times required by the project. Customers wait between 0 and 100 ms before entering the bank, teller-manager interaction for a withdrawal takes 5 to 30 ms, and the transaction in the safe takes 10 to 50 ms. Moreover, I made sure to note that blocking actions need output both before and after the wait, and that shared resource access like the manager and safe should have three messages: going there, using it, and finishing with it.

especially, I followed the project suggestion of starting small and testing with fewer threads first before scaling up. That makes it easier to catch synchronization mistakes before running the full 50-customer version. eventually, once the smaller version works, the final step is to run the complete simulation, verify that all customers are served, and make sure the bank closes only after all 50 customers have left.