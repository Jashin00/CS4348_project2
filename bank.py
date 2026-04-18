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


def log(thread_type, thread_id, partner, msg, colon=True):
    """Format output to match the sample style."""
    if colon:
        safe_print(f"{thread_type} {thread_id} [{partner}]: {msg}")
    else:
        safe_print(f"{thread_type} {thread_id} [{partner}] {msg}")


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

        # Teller announces readiness and waits for a customer
        log("Teller", self.teller_id, "", "ready to serve")
        log("Teller", self.teller_id, "", "waiting for a customer")

        # Bank opens only when all tellers are ready
        with teller_ready_lock:
            teller_ready_count += 1
            if teller_ready_count == NUM_TELLERS:
                bank_open_event.set()

        while True:
            # Put this teller in the available teller queue
            available_tellers.put(self)

            # Wait until a customer selects this teller
            self.customer_arrived.acquire()
            if self.stop_flag:
                break

            log("Teller", self.teller_id, f"Customer {self.customer_id}", "serving a customer")

            # Let customer know teller is ready for introduction
            self.ready_for_intro.release()

            # Wait until customer introduces itself
            self.customer_identified.acquire()

            # Ask customer for the transaction
            log("Teller", self.teller_id, f"Customer {self.customer_id}", "asks for transaction")
            self.transaction_requested.release()

            # Wait for customer to provide deposit or withdrawal
            self.transaction_given.acquire()

            # Handle withdrawal requests through the manager first
            if self.transaction_type == "Withdraw":
                log("Teller", self.teller_id, f"Customer {self.customer_id}", "handling withdrawal transaction")
                log("Teller", self.teller_id, f"Customer {self.customer_id}", "going to the manager")
                with manager_sem:
                    log("Teller", self.teller_id, f"Customer {self.customer_id}", "getting manager's permission")
                    time.sleep(random.uniform(0.005, 0.03))
                    log("Teller", self.teller_id, f"Customer {self.customer_id}", "got manager's permission")
            else:
                log("Teller", self.teller_id, f"Customer {self.customer_id}", "handling deposit transaction")

            # All transactions must go through the safe
            log("Teller", self.teller_id, f"Customer {self.customer_id}", "going to safe")
            with safe_sem:
                log("Teller", self.teller_id, f"Customer {self.customer_id}", "enter safe")
                time.sleep(random.uniform(0.01, 0.05))
                log("Teller", self.teller_id, f"Customer {self.customer_id}", "leaving safe")

            # Announce the transaction is finished
            if self.transaction_type == "Withdraw":
                log("Teller", self.teller_id, f"Customer {self.customer_id}", "finishes withdrawal transaction.")
            else:
                log("Teller", self.teller_id, f"Customer {self.customer_id}", "finishes deposit transaction.")

            # Tell customer thread it may leave the teller now
            log("Teller", self.teller_id, f"Customer {self.customer_id}", "wait for customer to leave.")
            self.transaction_complete.release()

            # Wait until the customer leaves the teller
            self.customer_left.acquire()
            self.left_ack.release()

            # Reset teller-specific customer data
            self.customer_id = None
            self.transaction_type = None

            # Teller becomes available again
            log("Teller", self.teller_id, "", "ready to serve")
            log("Teller", self.teller_id, "", "waiting for a customer")

        log("Teller", self.teller_id, "", "leaving for the day")


class Customer(threading.Thread):
    def __init__(self, customer_id):
        super().__init__()
        self.customer_id = customer_id

        # Customer randomly chooses a transaction
        self.transaction = random.choice(["Deposit", "Withdraw"])

    def run(self):
        global customers_finished

        # Customer decides what type of transaction to perform
        if self.transaction == "Withdraw":
            log("Customer", self.customer_id, "", "wants to perform a withdrawal transaction")
        else:
            log("Customer", self.customer_id, "", "wants to perform a deposit transaction")

        # Simulate customer arriving at a random time
        time.sleep(random.uniform(0, 0.1))

        # Customer cannot enter before the bank is open
        bank_open_event.wait()

        log("Customer", self.customer_id, "", "going to bank.")

        # Only 2 customers can pass through the door at the same time
        with door_sem:
            log("Customer", self.customer_id, "", "entering bank.")
            log("Customer", self.customer_id, "", "getting in line.")

            # Get a teller that is currently ready
            teller = available_tellers.get()

            log("Customer", self.customer_id, "", "selecting a teller.")
            log("Customer", self.customer_id, f"Teller {teller.teller_id}", "selects teller")

            # Tell the teller this customer has arrived
            teller.customer_id = self.customer_id
            teller.customer_arrived.release()

            # Wait until teller is ready before introducing self
            teller.ready_for_intro.acquire()
            log("Customer", self.customer_id, f"Teller {teller.teller_id}", "introduces itself", colon=False)
            teller.customer_identified.release()

            # Wait for teller to ask for transaction
            teller.transaction_requested.acquire()

            # Give the transaction to the teller
            if self.transaction == "Withdraw":
                log("Customer", self.customer_id, f"Teller {teller.teller_id}", "asks for withdrawal transaction")
            else:
                log("Customer", self.customer_id, f"Teller {teller.teller_id}", "asks for deposit transaction")

            teller.transaction_type = self.transaction
            teller.transaction_given.release()

            # Wait until teller finishes the transaction
            teller.transaction_complete.acquire()

            # Leave teller after transaction is finished
            log("Customer", self.customer_id, f"Teller {teller.teller_id}", "leaves teller")
            teller.customer_left.release()

            # Wait until teller confirms customer left
            teller.left_ack.acquire()
            log("Customer", self.customer_id, "", "goes to door")
            log("Customer", self.customer_id, "", "leaves the bank")

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

    # Wait until all tellers are ready and the bank is open
    bank_open_event.wait()
    
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

    safe_print("The bank closes for the day.")


if __name__ == "__main__":
    main()