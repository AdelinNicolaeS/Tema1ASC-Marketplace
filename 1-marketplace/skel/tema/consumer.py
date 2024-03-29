"""
This module represents the Consumer.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

from threading import Thread
import time
import sys

class Consumer(Thread):
    """
    Class that represents a consumer.
    """

    def __init__(self, carts, marketplace, retry_wait_time, **kwargs):
        """
        Constructor.

        :type carts: List
        :param carts: a list of add and remove operations

        :type marketplace: Marketplace
        :param marketplace: a reference to the marketplace

        :type retry_wait_time: Time
        :param retry_wait_time: the number of seconds that a producer must wait
        until the Marketplace becomes available

        :type kwargs:
        :param kwargs: other arguments that are passed to the Thread's __init__()
        """
        Thread.__init__(self, **kwargs)
        self.carts = carts
        self.marketplace = marketplace
        self.retry_wait_time = retry_wait_time
        self.name = kwargs.get("name")

    def run(self):
        for cart in self.carts:
            id_cart = self.marketplace.new_cart()

            for operation in cart:
                quantity = operation["quantity"]
                my_type = operation["type"]
                product = operation["product"]
                contor = 0
                while contor < quantity:
                    # we apply add until it succeds 'quantity' times
                    if my_type == "add":
                        if self.marketplace.add_to_cart(id_cart, product):
                            contor = contor + 1
                        else:
                            time.sleep(self.retry_wait_time)
                    # just applying remove 'quantity' times
                    else:
                        self.marketplace.remove_from_cart(id_cart, product)
                        contor = contor + 1
            placed_order = self.marketplace.place_order(id_cart)
            for each_p in placed_order:
                # flush necessary to get rid of junk data
                sys.stdout.flush()
                print(f"{self.name} bought {each_p}")
                