# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 24 July 2013
#
# Copyright 2012 Linkoping University
# -----------------------------------------------------------------------------

"""Implementation of a simple database class."""

import random


class Database(object):

    """Class containing a database implementation."""

    def __init__(self, db_file):
        self.db_file = db_file
        self.rand = random.Random()
        self.rand.seed()

        self.fortunes = []
        # Populate self.fortunes from self.db_file
        with open(self.db_file, "r") as f:
            line = f.readline()
            fortune = ""
            while line:
                if len(line) <= 2 and line[0] == "%":
                    self.fortunes.append(fortune)
                    fortune = ""
                else:
                    fortune += line
                line = f.readline()

    def read(self):
        """Read a random location in the database."""
        random_index = self.rand.randint(0, len(self.fortunes) - 1)
        return self.fortunes[random_index]

    def write(self, fortune):
        """Write a new fortune to the database."""   
        with open(self.db_file, "a") as f:
            f.write(fortune + "\n%\n")
        self.fortunes.append(fortune)
