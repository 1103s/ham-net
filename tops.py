"""
A simple module to hold the global lock for the sim.
"""
from queue import Queue
GLOBAL_RUN = Queue() # If this has content, we cant close the sim yet.
