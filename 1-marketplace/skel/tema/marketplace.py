#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

from threading import Lock
from time import gmtime
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(handlers=[
    RotatingFileHandler('marketplace.log', maxBytes=100000, backupCount=10)
],
                    level=logging.INFO,
                    format='[%(asctime)s] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')
logging.Formatter.converter = gmtime
logger = logging.getLogger()


class Marketplace:
    """
    Class that represents the Marketplace. It's the central part of the implementation.
    The producers and consumers use its methods concurrently.
    """

    def __init__(self, queue_size_per_producer):
        """
        Constructor

        :type queue_size_per_producer: Int
        :param queue_size_per_producer: the maximum size of a queue associated with each producer
        """

        logger.info(
            'The marketplace {} with maximum queue of {} is initializing...'.
            format(self, queue_size_per_producer))
        self.queue_size_per_producer = queue_size_per_producer
        self.product_to_producer = {}
        self.producer_to_products = {}
        self.carts = {}
        self.cart_counter = 0
        self.producer_counter = 0

        self.lock_register = Lock()
        self.lock_maximum_elements = Lock()
        self.lock_cart_size = Lock()
        self.lock_remove_from = Lock()

        logger.info('Initialization ended successfully!')

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """

        logger.info(f'Starting producer registration by {self}...')
        with self.lock_register:
            self.producer_to_products[self.producer_counter] = []
            self.producer_counter += 1
            logger.info(f'Producer with id: {self.producer_counter - 1} was created!')
            return self.producer_counter - 1

    def publish(self, producer_id, product):
        """
        Adds the product provided by the producer to the marketplace

        :type producer_id: String
        :param producer_id: producer id

        :type product: Product
        :param product: the Product that will be published in the Marketplace

        :returns True or False. If the caller receives False, it should wait and then try again.
        """

        logger.info(
            f'Providing product {product} by producer {producer_id} to marketplace {self}...')
        with self.lock_maximum_elements:
            if len(self.producer_to_products[producer_id]) \
                > self.queue_size_per_producer:
                logger.info('Providing product failed!')
                return False
            self.producer_to_products[producer_id].append(product)
            self.product_to_producer[product] = producer_id
        logger.info('Providing product ended successfully!')
        return True

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """

        with self.lock_cart_size:
            logger.info(f'Creating new cart by marketplace {self}...')
            self.carts[self.cart_counter] = []
            self.cart_counter += 1
            logger.info(
                f'A new cart with id {self.cart_counter - 1} was created!')
        return self.cart_counter - 1

    def add_to_cart(self, cart_id, product):
        """
        Adds a product to the given cart. The method returns

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to add to cart

        :returns True or False. If the caller receives False, it should wait and then try again
        """

        logger.info(
            f'Adding product {product} in the cart {cart_id} using marketplace {self}...')
        all_producers = self.producer_to_products.keys()
        for producer in all_producers:
            number_of_products = \
                self.producer_to_products[producer].count(product)
            if number_of_products > 0:
                self.carts[cart_id].append(product)
                self.producer_to_products[producer].remove(product)
                logger.info('Adding a new product ended successfully!')
                return True
        logger.info('Adding a new product failed!')
        return False

    def remove_from_cart(self, cart_id, product):
        """
        Removes a product from cart.

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to remove from cart
        """

        logger.info(
            f'Removing product {product} from the cart {cart_id} using marketplace {self}...')
        producer = self.product_to_producer[product]
        with self.lock_remove_from:
            self.carts[cart_id].remove(product)
            self.producer_to_products[producer].append(product)
        logger.info('Removing a new product ended successfully!')

    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """

        logger.info(f'Placing a new order from cart {cart_id} using marketplace {self}')
        final_order = self.carts.pop(cart_id, None)
        logger.info(f'The order {final_order} was provided!')
        return final_order
