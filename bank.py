import threading
import time
import random
from queue import Queue

# Project constants
NUM_TELLERS = 3
NUM_CUSTOMERS = 50

# Bank opens only after all tellers are ready
bank_open_event = threading.Event()
teller_ready_count = 0
teller_ready_lock = threading.Lock()

# Shared resources
# Only 2 customers can enter through the door at a time
door_sem = threading.Semaphore(2)

# Only 2 tellers can be in the safe at the same time
safe_sem = threading.Semaphore(2)

# Only 1 teller can talk to the manager at a time
manager_sem = threading.Semaphore(1)

# Queue of tellers currently available to help a customer
available_tellers = Queue()

# Lock to keep print output from mixing between threads
print_lock = threading.Lock()

# Counter for customers who finish the full process
customers_finished = 0
customers_finished_lock = threading.Lock()


def safe_print(msg):
    """Print one full line at a time so thread output does not overlap."""
    with print_lock:
        print(msg, flush=True)


def log(thread_type, thread_id, partner, msg):
    """Format output to match the project style."""
    safe_print(f"{thread_type} {thread_id} [{partner}]: {msg}")


class Teller(threading.Thread):
    def __init__(self, teller_id):
        super().__init__()
        self.teller_id = teller_id

        # Shared info between this teller and the current customer
        self.customer_id = None
        self.transaction_type = None

        # Semaphores used to synchronize one teller with one customer
        self.customer_arrived = threading.Semaphore(0)
        self.customer_identified = threading.Semaphore(0)
        self.transaction_requested = threading.Semaphore(0)
        self.transaction_given = threading.Semaphore(0)
        self.transaction_complete = threading.Semaphore(0)
        self.customer_left = threading.Semaphore(0)

        # Used so the customer waits until teller confirms customer left
        self.left_ack = threading.Semaphore(0)

        # Used so the customer does not introduce itself before the teller is ready
        self.ready_for_intro = threading.Semaphore(0)

        self.stop_flag = False

    def run(self):
        global teller_ready_count

        # Teller announces readiness
        log("Teller", self.teller_id, f"Teller {self.teller_id}", "ready to serve")

        # Bank opens only when all tellers are ready
        with teller_ready_lock:
            teller_ready_count += 1
            if teller_ready_count == NUM_TELLERS:
                safe_print("Bank is now open.")
                bank_open_event.set()

        while True:
            # Put this teller in the available teller queue
            available_tellers.put(self)

            # Wait until a customer selects this teller
            self.customer_arrived.acquire()
            if self.stop_flag:
                break

            log("Teller", self.teller_id, f"Customer {self.customer_id}", "calls next customer")
            log("Teller", self.teller_id, f"Customer {self.customer_id}", "waits for customer to approach")

            # Let customer know teller is ready for introduction
            self.ready_for_intro.release()

            # Wait until customer introduces itself
            self.customer_identified.acquire()

            # Ask customer for the transaction
            log("Teller", self.teller_id, f"Customer {self.customer_id}", "asks for transaction")
            self.transaction_requested.release()

            # Wait for customer to provide deposit or withdraw
            self.transaction_given.acquire()
            log(
                "Teller",
                self.teller_id,
                f"Customer {self.customer_id}",
                f"receives {self.transaction_type} transaction"
            )

            # Withdrawals must go to the manager first
            if self.transaction_type == "Withdraw":
                log("Teller", self.teller_id, f"Customer {self.customer_id}", "going to manager")
                with manager_sem:
                    log("Teller", self.teller_id, f"Customer {self.customer_id}", "talking to manager")
                    time.sleep(random.uniform(0.005, 0.03))
                    log("Teller", self.teller_id, f"Customer {self.customer_id}", "done with manager")

            # All transactions must go to the safe
            log("Teller", self.teller_id, f"Customer {self.customer_id}", "going to safe")
            with safe_sem:
                log("Teller", self.teller_id, f"Customer {self.customer_id}", "using safe")
                log("Teller", self.teller_id, f"Customer {self.customer_id}", "transaction in safe starts")
                time.sleep(random.uniform(0.01, 0.05))
                log("Teller", self.teller_id, f"Customer {self.customer_id}", "transaction in safe ends")
            log("Teller", self.teller_id, f"Customer {self.customer_id}", "done with safe")

            # Tell customer the transaction is complete
            log("Teller", self.teller_id, f"Customer {self.customer_id}", "transaction complete")
            self.transaction_complete.release()

            # Wait until the customer leaves the teller
            self.customer_left.acquire()
            log("Teller", self.teller_id, f"Customer {self.customer_id}", "customer left teller")
            self.left_ack.release()

            # Reset teller-specific customer data
            self.customer_id = None
            self.transaction_type = None

        log("Teller", self.teller_id, f"Teller {self.teller_id}", "done for the day")


class Customer(threading.Thread):
    def __init__(self, customer_id):
        super().__init__()
        self.customer_id = customer_id

        # Customer randomly chooses a transaction
        self.transaction = random.choice(["Deposit", "Withdraw"])

    def run(self):
        global customers_finished

        log("Customer", self.customer_id, f"Customer {self.customer_id}", f"decides on {self.transaction}")

        # Simulate customer arriving at a random time
        log("Customer", self.customer_id, f"Customer {self.customer_id}", "arrives at bank")
        time.sleep(random.uniform(0, 0.1))
        log("Customer", self.customer_id, f"Customer {self.customer_id}", "waiting to enter bank")

        # Customer cannot enter before the bank is open
        bank_open_event.wait()

        # Only 2 customers can pass through the door at the same time
        with door_sem:
            log("Customer", self.customer_id, f"Customer {self.customer_id}", "enters bank")
            log("Customer", self.customer_id, f"Customer {self.customer_id}", "gets in line")

            # Get a teller that is currently ready
            teller = available_tellers.get()

            log("Customer", self.customer_id, f"Teller {teller.teller_id}", "selects teller")

            # Tell the teller this customer has arrived
            teller.customer_id = self.customer_id
            teller.customer_arrived.release()

            # Wait until teller is ready before introducing self
            teller.ready_for_intro.acquire()
            log("Customer", self.customer_id, f"Teller {teller.teller_id}", "introduces itself")
            teller.customer_identified.release()

            # Wait for teller to ask for transaction
            teller.transaction_requested.acquire()

            # Give the transaction to the teller
            log("Customer", self.customer_id, f"Teller {teller.teller_id}", f"tells transaction {self.transaction}")
            teller.transaction_type = self.transaction
            teller.transaction_given.release()

            # Wait until teller finishes the transaction
            log("Customer", self.customer_id, f"Teller {teller.teller_id}", "waits for transaction to complete")
            teller.transaction_complete.acquire()

            # Leave teller after transaction is finished
            log("Customer", self.customer_id, f"Teller {teller.teller_id}", "left teller")
            teller.customer_left.release()

            # Wait until teller confirms customer left
            teller.left_ack.acquire()
            log("Customer", self.customer_id, f"Customer {self.customer_id}", "leaving the bank")

        # Count this customer as fully served
        with customers_finished_lock:
            customers_finished += 1


def main():
    # Create teller and customer threads
    tellers = [Teller(i) for i in range(NUM_TELLERS)]
    customers = [Customer(i) for i in range(NUM_CUSTOMERS)]

    # Start all tellers first
    for teller in tellers:
        teller.start()

    # Start all customers
    for customer in customers:
        customer.start()

    # Wait for all customers to finish
    for customer in customers:
        customer.join()

    # Stop teller threads after all customers are done
    for teller in tellers:
        teller.stop_flag = True
        teller.customer_arrived.release()

    for teller in tellers:
        teller.join()

    safe_print("Bank is now closed.")
    safe_print(f"Total customers served: {customers_finished}")


if __name__ == "__main__":
    main()