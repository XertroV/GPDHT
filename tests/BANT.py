from datastructs import BANT

from hashlib import sha256
import unittest, os, json

def dohash(msg):
	return BANT(sha256(str(msg)).digest())

genesisheader = BANT("0100000000000000000000000000000000000000000000000000000000000000000000003ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a29ab5f49ffff001d1dac2b7c", True)
print genesisheader
print dohash(dohash(genesisheader))

class Test_BANT(unittest.TestCase):
	def test_hash(self):
		self.assertEqual(1,2)
