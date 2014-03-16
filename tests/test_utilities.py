from utilities import *

import unittest, os, json, math

class Test_Utilities(unittest.TestCase):
	def test_num2bits(self):
		self.assertEqual(num2bits(0), [])
		self.assertEqual(num2bits(1), [1])
		self.assertEqual(num2bits(2), [1,0])
		self.assertEqual(num2bits(3), [1,1])
		self.assertEqual(num2bits(8), [1,0,0,0])
		self.assertEqual(num2bits(5), [1,0,1])
		self.assertEqual(num2bits(128), [1,0,0,0,0,0,0,0])
