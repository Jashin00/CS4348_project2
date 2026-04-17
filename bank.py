import threading
import time
import random
from queue import Queue

NUM_TELLERS = 3
NUM_CUSTOMERS = 10   # keep small for testing first

bank_open_event = threading.Event()
teller_ready_count = 0
teller_ready_lock = threading.Lock()

door_sem = threading.Semaphore(2)
available_tellers = Queue()

print_lock = threading.Lock()


def safe_print(msg):
    with print_lock:
        print(msg, flush=True)


def log(thread_type, thread_id, partner, msg):
    safe_print(f"{thread_type} {thread_id} [{partner}]: {msg}")


class Teller(threading.Thread):
    def __init__(self, teller_id):
        super().__init__()
        self.teller_id = teller_id

        self.customer_id = None
        self.transaction_type = None

        self.customer_arrived = threading.Semaphore(0)
        self.customer_identified = threading.Semaphore(0)
        self.transaction_requested = threading.Semaphore(0)
        self.transaction_given = threading.Semaphore(0)
        self.transaction_complete = threading.Semaphore(0)
        self.customer_left = threading.Semaphore(0)

        self.stop_flag = False

    def run(self):
        global teller_ready_count

        log("Teller", self.teller_id, f"Teller {self.teller_id}", "ready to serve")

        with teller_ready_lock:
            teller_ready_count += 1
            if teller_ready_count == NUM_TELLERS:
                safe_print("Bank is now open.")
                bank_open_event.set()

        while True:
            # teller announces availability
            available_tellers.put(self)

            # wait for customer to approach
            self.customer_arrived.acquire()
            if self.stop_flag:
                break

            log("Teller", self.teller_id, f"Customer {self.customer_id}", "calls next customer")
            log("Teller", self.teller_id, f"Customer {self.customer_id}", "waits for customer to approach")

            # wait for customer to identify itself
            self.customer_identified.acquire()

            # ask for transaction
            log("Teller", self.teller_id, f"Customer {self.customer_id}", "asks for transaction")
            self.transaction_requested.release()

            # wait until customer gives transaction
            self.transaction_given.acquire()
            log("Teller", self.teller_id, f"Customer {self.customer_id}",
                f"receives {self.transaction_type} transaction")

            # basic transaction work for session 2
            log("Teller", self.teller_id, f"Customer {self.customer_id}", "starts transaction")
            time.sleep(0.02)
            log("Teller", self.teller_id, f"Customer {self.customer_id}", "transaction complete")

            # inform customer it is done
            self.transaction_complete.release()

            # wait for customer to leave teller
            self.customer_left.acquire()
            log("Teller", self.teller_id, f"Customer {self.customer_id}", "customer left teller")

            # reset for next customer
            self.customer_id = None
            self.transaction_type = None

        log("Teller", self.teller_id, f"Teller {self.teller_id}", "done for the day")


class Customer(threading.Thread):
    def __init__(self, customer_id):
        super().__init__()
        self.customer_id = customer_id
        self.transaction = random.choice(["Deposit", "Withdraw"])

    def run(self):
        # customer waits between 0 and 100 ms before entering
        delay = random.uniform(0, 0.1)
        log("Customer", self.customer_id, f"Customer {self.customer_id}", "waiting before entering bank")
        time.sleep(delay)
        log("Customer", self.customer_id, f"Customer {self.customer_id}", "done waiting before entering bank")

        # cannot enter before bank opens
        bank_open_event.wait()

        log("Customer", self.customer_id, f"Customer {self.customer_id}",
            f"wants {self.transaction}")
        log("Customer", self.customer_id, f"Customer {self.customer_id}", "waiting to enter bank")

        # only 2 customers can enter through door at a time
        with door_sem:
            log("Customer", self.customer_id, f"Customer {self.customer_id}", "enters bank")
            log("Customer", self.customer_id, f"Customer {self.customer_id}", "gets in line")

            # if a teller is ready, customer goes immediately
            teller = available_tellers.get()

            log("Customer", self.customer_id, f"Teller {teller.teller_id}", "selects teller")

            # approach teller
            teller.customer_id = self.customer_id
            teller.customer_arrived.release()

            log("Customer", self.customer_id, f"Teller {teller.teller_id}", "introduces itself")
            teller.customer_identified.release()

            # wait for teller to ask for transaction
            teller.transaction_requested.acquire()

            # tell teller the transaction
            log("Customer", self.customer_id, f"Teller {teller.teller_id}",
                f"tells transaction {self.transaction}")
            teller.transaction_type = self.transaction
            teller.transaction_given.release()

            # wait for teller to complete transaction
            log("Customer", self.customer_id, f"Teller {teller.teller_id}", "waits for transaction to complete")
            teller.transaction_complete.acquire()

            log("Customer", self.customer_id, f"Teller {teller.teller_id}", "left teller")
            teller.customer_left.release()

            time.sleep(0.001)

            log("Customer", self.customer_id, f"Customer {self.customer_id}", "leaving the bank through door")


def main():
    tellers = [Teller(i) for i in range(NUM_TELLERS)]
    customers = [Customer(i) for i in range(NUM_CUSTOMERS)]

    for teller in tellers:
        teller.start()

    for customer in customers:
        customer.start()

    for customer in customers:
        customer.join()

    for teller in tellers:
        teller.stop_flag = True
        teller.customer_arrived.release()

    for teller in tellers:
        teller.join()

    safe_print("Session 2 teller-customer synchronization complete.")


if __name__ == "__main__":
    main()