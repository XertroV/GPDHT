from datastructs import *

from hashlib import sha256
import unittest, os, json


def sha256hash(msg):
	return BANT(sha256(str(msg)).digest())
def dsha256(msg):
	return sha256hash(sha256hash(msg))



z32 = BANT('', padTo=32)
z32HN = FakeHashNode(z32, 0)

class Test_HashTree(unittest.TestCase):
	def test_hashNode(self):
		testVectors = [
			( hashfunc(z32.concat(BANT('\x00').concat(z32))), BANT('98ce42deef51d40269d542f5314bef2c7468d401ad5d85168bfab4c0108f75f7', True) ),
			( HashNode([z32HN, z32HN], 1).getHash(), BANT('98ce42deef51d40269d542f5314bef2c7468d401ad5d85168bfab4c0108f75f7', True) )
		]
		
		for pair in testVectors:
			self.assertEqual(pair[0], pair[1])
		
		
		
	def test_hashTree(self):
		a = HashTree([z32,z32])	
		abcd = HashTree([BANT(i) for i in ['a','b','c','d']])
		abc = HashTree([BANT(i) for i in ['a','b','c']])
		abdd = HashTree([BANT(i) for i in ['a','b','d','d']])
		testVectors = [
			( HashTree([z32HN,z32HN]).getHash(), BANT('98ce42deef51d40269d542f5314bef2c7468d401ad5d85168bfab4c0108f75f7', True) ),
			( HashTree([z32,z32]).getHash(), BANT('24585a8ee00325799523c26a6c99467682ee561fd6a2e5a3d9088c0611da61b0', True) ),
			( abcd.getHash(), BANT('5f3bc542cfb30539c3ab40901df086dfec9c911279ce4f8f2541da1cc54588da', True)),
			
		]
		
		for pair in testVectors:
			self.assertEqual(pair[0], pair[1])
		
		abc.append(BANT('d'))		
		self.assertEqual(abc, abcd)
	
		abc.update(2, BANT('d'))
		self.assertEqual(abc, abdd)
		
			
		a.append(z32)
		
		self.assertEqual(a.getHash(), BANT('dbcf217028b8a85846f19d88ccae3eeed90e77dc93ef280e37a7d41700001421', True))


class Test_BANT(unittest.TestCase):
	def test_hash(self):
		genesisheader = BANT("0100000000000000000000000000000000000000000000000000000000000000000000003ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a29ab5f49ffff001d1dac2b7c", True)
		self.assertEqual(dsha256(genesisheader).str(), "6fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000".decode('hex'))
		
		
	def test_BANT_Padding(self):
		self.assertEqual(BANT('\xff', padTo=6), BANT('\x00\x00\x00\x00\x00\xff'))
		self.assertEqual(BANT('\xff\xff\xff', padTo=1), BANT('\xff\xff\xff'))
		
		
	def test_RLP_SERIALIZE(self):
		testVectors = [
			(BANT(b'dog'), BANT(b'\x83dog')),
			([BANT(b'dog'), BANT(b'cat')], BANT(b'\xc8\x83dog\x83cat')),
			(BANT(''), BANT(b'\x80')),
			(BANT(i2s(15)), BANT(b'\x0f')),
			(BANT(i2s(1024)), BANT(b'\x82\x04\x00')),
			([ [], [[]], [ [], [[]] ] ], BANT(b'\xc7\xc0\xc1\xc0\xc3\xc0\xc1\xc0'))
		]
		
		for pair in testVectors:
			self.assertEqual(RLP_SERIALIZE(pair[0]), pair[1])
			self.assertEqual(RLP_DESERIALIZE(pair[1]), pair[0])
			
	def test_BANT_Operations(self):
		testVectors = [
			(BANT('\x01') + BANT('\x00\x00'), BANT('\x00\x01')),
		]
		
		for p in testVectors:
			self.assertEqual(p[0], p[1])
			
			
	def test_ADDBYTEARRAYS(self):
		tv = [
			(ADDBYTEARRAYS(bytearray('\x00\x00'), bytearray('\x01')), bytearray('\x00\x01')),
			(ADDBYTEARRAYS(bytearray('\x00'), bytearray('\x01')), bytearray('\x01')),
			(ADDBYTEARRAYS(bytearray('\xff'), bytearray('\x01')), bytearray('\x01\x00')),
			(ADDBYTEARRAYS(bytearray('\x00\x00\xff'), bytearray('\x01')), bytearray('\x00\x01\x00')),
			(ADDBYTEARRAYS(bytearray('\xff\x00'), bytearray('\x01')), bytearray('\xff\x01')),
			(ADDBYTEARRAYS(bytearray('\xff\x00'), bytearray('\xff\x00')), bytearray('\x01\xfe\x00')),
			(ADDBYTEARRAYS(bytearray('\x00\xff\x00'), bytearray('\xff\x00')), bytearray('\x01\xfe\x00')),
			(ADDBYTEARRAYS(bytearray(b'\x8e\xa7\x16q\xa6\xed\xd9\x87\xad\x9e\x90\x97B\x8f\xc3\xf1i\xde\xcb\xa3\xac\x8f\x10\xda{$\xe0\xca\x16\x80\xff\xff'), bytearray('\x01')), bytearray(b'\x8e\xa7\x16q\xa6\xed\xd9\x87\xad\x9e\x90\x97B\x8f\xc3\xf1i\xde\xcb\xa3\xac\x8f\x10\xda{$\xe0\xca\x16\x81\x00\x00'))
		]
		for p in tv:
			self.assertEqual(p[0], p[1])
