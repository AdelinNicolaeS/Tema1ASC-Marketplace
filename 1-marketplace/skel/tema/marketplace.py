#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""
import unittest
from threading import Lock
from time import gmtime

import logging
from logging.handlers import RotatingFileHandler

from tema.producer import Producer
from tema.consumer import Consumer
from tema.product import Coffee, Tea

# https://stackoverflow.com/questions/40088496/how-to-use-pythons-rotatingfilehandler

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
            'The marketplace %s with maximum queue of %s is initializing...',
            self, queue_size_per_producer)
        self.queue_size_per_producer = queue_size_per_producer
        self.product_to_producer = {} # dictionary for (product, producer_id)
        self.producer_to_products = {} # dictionary for (producer_id, [product1, product2, ...])
        self.carts = {} # dictionary for (cart_id, [product1, product2, ...])
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

        logger.info('Starting producer registration by %s...', self)
        with self.lock_register:
            # using lock to increment atomically producer_counter
            self.producer_to_products[self.producer_counter] = []
            self.producer_counter += 1
            logger.info('Producer with id: %d was created!',
                        self.producer_counter - 1)
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

        logger.info("Providing product %s by producer %s to marketplace %s...",
                    product, producer_id, self)
        with self.lock_maximum_elements:
            # using lock to get and compare correctly the lengths
            if len(self.producer_to_products[producer_id]) \
                >= self.queue_size_per_producer:
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
            # using lock to increment atomically cart_counter
            logger.info('Creating new cart by marketplace %s...', self)
            self.carts[self.cart_counter] = []
            self.cart_counter += 1
            logger.info('A new cart with id %d was created!',
                        self.cart_counter - 1)
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

        logger.info('Adding product %s in the cart %s using marketplace %s...',
                    product, cart_id, self)
        # take all the producers from map
        all_producers = self.producer_to_products.keys()
        for producer in all_producers:
            number_of_products = \
                self.producer_to_products[producer].count(product)
            # if product is created by this producer
            if number_of_products > 0:
                # put it in the cart and remove from product's list
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
            'Removing product %s from the cart %s using marketplace %s...',
            product, cart_id, self)
        # taking producer using our dictionary
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

        logger.info('Placing a new order from cart %s using marketplace %s',
                    cart_id, self)
        # take the information from cart and remove the cart from dictionary
        final_order = self.carts.pop(cart_id, None)
        logger.info('The order %s was provided!', final_order)
        return final_order


class TestMarketplace(unittest.TestCase):
    """Class that tests the whole process created by Marketplace"""

    def setUp(self):
        """Initialization for main attributes of class"""
        self.size_marketplace = 2

        self.marketplace = Marketplace(self.size_marketplace)
        self.consumer0 = Consumer(carts=[],
                                  marketplace=self.marketplace,
                                  retry_wait_time=100,
                                  kwargs=dict({"name": "consumer0"}))
        self.consumer1 = Consumer(carts=[],
                                  marketplace=self.marketplace,
                                  retry_wait_time=250,
                                  kwargs=dict({"name": "consumer1"}))
        self.product0 = Coffee('Arabica', 12, 6, 'MEDIUM')
        self.product1 = Coffee('Cappucino', 10, 12, 'LOW')
        self.product2 = Tea('Complex', 9, 'White')
        self.product3 = Tea('Honey tea', 11, 'Sweet')
        self.producer0 = Producer(products=[],
                                  marketplace=self.marketplace,
                                  republish_wait_time=120,
                                  kwargs={})
        self.producer1 = Producer(products=[],
                                  marketplace=self.marketplace,
                                  republish_wait_time=176,
                                  kwargs={})

    def test___init__(self):
        """Test function which tests if __init__ runs correctly"""
        self.assertEqual(self.marketplace.queue_size_per_producer,
                         self.size_marketplace)
        self.assertEqual(self.marketplace.cart_counter, 0)
        self.assertEqual(self.marketplace.producer_counter, 2)
        self.assertEqual(self.producer0.id_producer, 0)
        self.assertEqual(self.producer1.id_producer, 1)

    def test_register_producer(self):
        """Test function which tests if register_producer runs correctly"""
        self.assertEqual(self.marketplace.register_producer(), 2)
        self.assertEqual(self.marketplace.producer_counter, 3)

    def test_publish(self):
        """Test function which tests if publish runs correctly"""
        self.assertEqual(self.marketplace.publish(0, self.product1), True)
        self.assertEqual(self.marketplace.publish(0, self.product2), True)
        self.assertEqual(self.marketplace.publish(0, self.product3), False)
        self.assertEqual(self.marketplace.publish(1, self.product0), True)
        self.assertEqual(self.marketplace.publish(1, self.product3), True)

    def test_new_cart(self):
        """Test function which tests if new_cart runs correctly"""
        self.assertEqual(self.marketplace.new_cart(), 0)
        self.assertEqual(self.marketplace.new_cart(), 1)
        self.assertEqual(self.marketplace.new_cart(), 2)

    def test_add_to_cart(self):
        """Test function which tests if add_to_cart runs correctly"""
        self.marketplace.new_cart()
        self.marketplace.new_cart()
        self.marketplace.new_cart()
        self.marketplace.publish(0, self.product1)
        self.marketplace.publish(0, self.product2)
        self.marketplace.publish(1, self.product0)
        self.marketplace.publish(1, self.product3)

        self.assertTrue(self.marketplace.add_to_cart(0, self.product0))
        self.assertFalse(self.marketplace.add_to_cart(1, self.product0))
        self.assertTrue(self.marketplace.add_to_cart(0, self.product1))
        self.assertTrue(self.marketplace.add_to_cart(0, self.product3))
        self.assertTrue(self.marketplace.add_to_cart(1, self.product2))

    def test_remove_from_cart(self):
        """Test function which tests if remove_the_cart runs correctly"""
        self.marketplace.new_cart()
        self.marketplace.new_cart()
        self.marketplace.new_cart()
        self.marketplace.publish(0, self.product1)
        self.marketplace.publish(0, self.product2)
        self.marketplace.publish(1, self.product0)
        self.marketplace.publish(1, self.product3)
        self.marketplace.add_to_cart(0, self.product0)
        self.marketplace.add_to_cart(0, self.product1)
        self.marketplace.add_to_cart(0, self.product3)
        self.marketplace.add_to_cart(1, self.product2)

        self.marketplace.remove_from_cart(1, self.product2)
        self.assertFalse(self.product2 in self.marketplace.carts[1])

        self.marketplace.remove_from_cart(0, self.product3)
        self.assertFalse(self.product3 in self.marketplace.carts[0])

    def test_place_order(self):
        """Test function which tests if place_order runs correctly"""
        self.marketplace.new_cart()
        self.marketplace.new_cart()
        self.marketplace.new_cart()
        self.marketplace.publish(0, self.product1)
        self.marketplace.publish(0, self.product2)
        self.marketplace.publish(1, self.product0)
        self.marketplace.publish(1, self.product3)
        self.marketplace.add_to_cart(0, self.product0)
        self.marketplace.add_to_cart(0, self.product1)
        self.marketplace.add_to_cart(0, self.product3)
        self.marketplace.add_to_cart(1, self.product2)
        self.marketplace.remove_from_cart(1, self.product2)
        self.marketplace.remove_from_cart(0, self.product3)

        self.assertEqual(self.marketplace.place_order(0),
                         [self.product0, self.product1])
        self.assertEqual(len(self.marketplace.place_order(1)), 0)
        self.assertEqual(len(self.marketplace.place_order(2)), 0)
