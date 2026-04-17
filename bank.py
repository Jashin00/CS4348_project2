
import threading
import time
import random
from queue import Queue

NUM_TELLERS = 3
NUM_CUSTOMERS = 10   # start small for testing

bank_open_event = threading.Event()
teller_ready_count = 0
teller_ready_lock = threading.Lock()

customer_line = Queue()
door_sem = threading.Semaphore(2)

print_lock = threading.Lock()

def safe_print(msg):
    with print_lock:
        print(msg, flush=True)

def log(thread_type, thread_id, partner, msg):
    if partner is None:
        safe_print(f"{thread_type} {thread_id} [{thread_type} {thread_id}]: {msg}")
    else:
        safe_print(f"{thread_type} {thread_id} [{partner}]: {msg}")


class Teller(threading.Thread):
    def __init__(self, teller_id):
        super().__init__()
        self.teller_id = teller_id

    def run(self):
        global teller_ready_count

        log("Teller", self.teller_id, f"Teller {self.teller_id}", "ready to serve")

        with teller_ready_lock:
            teller_ready_count += 1
            if teller_ready_count == NUM_TELLERS:
                safe_print("Bank is now open.")
                bank_open_event.set()

        while True:
            customer_id = customer_line.get()
            if customer_id is None:
                break

            log("Teller", self.teller_id, f"Customer {customer_id}", "calls next customer")
            time.sleep(0.01)

        log("Teller", self.teller_id, f"Teller {self.teller_id}", "done for the day")


class Customer(threading.Thread):
    def __init__(self, customer_id):
        super().__init__()
        self.customer_id = customer_id
        self.transaction = random.choice(["Deposit", "Withdraw"])

    def run(self):
        time.sleep(random.uniform(0, 0.1))

        bank_open_event.wait()

        log("Customer", self.customer_id, f"Customer {self.customer_id}",
            f"wants {self.transaction}")

        log("Customer", self.customer_id, f"Customer {self.customer_id}", "waiting to enter bank")
        with door_sem:
            log("Customer", self.customer_id, f"Customer {self.customer_id}", "enters bank")
            log("Customer", self.customer_id, f"Customer {self.customer_id}", "gets in line")
            customer_line.put(self.customer_id)
            time.sleep(0.01)




def main():
    tellers = [Teller(i) for i in range(NUM_TELLERS)]
    customers = [Customer(i) for i in range(NUM_CUSTOMERS)]

    for t in tellers:
        t.start()

    for c in customers:
        c.start()

    for c in customers:
        c.join()

    for _ in tellers:
        customer_line.put(None)

    for t in tellers:
        t.join()

    print("Session 1 basic interaction between teller and costumer complete complete.")


if __name__ == "__main__":
    main()