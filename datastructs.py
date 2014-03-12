
from hashlib import sha256
from utilities import *

from bitcoin.base58 import encode as b58encode, decode as b58decode


def hashfunc(msg):
	return sha256(msg).digest()

eba = bytearray('')
def ADDBYTEARRAYS(a,b,carry=0):
	if (a == eba or b == eba) and carry == 0: return a + b
	if a == eba and b == eba and carry == 1: return bytearray([carry])
	elif a == eba: return b[:-1] + bytearray([b[-1] + carry])
	elif b == eba: return a[:-1] + bytearray([a[-1] + carry])
	s = a[-1] + b[-1] + carry
	d = s % 256
	c = s/256
	return ADDBYTEARRAYS(a[:-1],b[:-1],c) + bytearray([d])

class BANT:
	'''Byte Array Number Thing
	Special data structure where it acts as a number and a byte array/list
	Slices like a byte array
	Adds and compares like a number
	Hashes like a byte array
	'''
	def __init__(self, initString=b'\x00', fromHex=False):
		if fromHex == True:
			'''input should be a string in hex encoding'''
			self.this = bytearray(initString.decode('hex')) # byte array
		elif isinstance(initString, int):
			self.this = bytearray(i2s(initString))
		else:
			self.this = bytearray(bytes(initString))
		self.isBANT = True
	
		
	def __lt__(self, other):
		return int(self) < int(other)
	def __gt__(self, other):
		return int(self) > int(other)
	def __eq__(self, other):
		if isinstance(other, str):
			return self.this == other
		return int(self) == int(other)
	def __ne__(self, other):
		return int(self) != int(other)
	def __le__(self, other):
		return int(self) <= int(other)
	def __ge__(self, other):
		return int(self) >= int(other)
	def __cmp__(self, other):
		return int(self) - int(other)
		
	def __len__(self):
		return len(self.this)
	def __getitem__(self,key):
		return BANT(self.this[key])
	def __setitem__(self,key,value):
		self.this[key] = value
		
	# do I need to do the r___ corresponding functions? (__radd__ for example)
	def __add__(self, other):
		return BANT(ADDBYTEARRAYS(self.this, other.this))
	def __sub__(self, other):
		return BANT(i2h(int(self) - int(other)))
	def __mul__(self, other):
		return BANT(i2h(int(self) * int(other)))
	def __div__(self, other):
		return BANT(i2h(int(self) / int(other)))
	def __mod__(self, other):
		return BANT(i2h(int(self) % int(other)))
	def __pow__(self, other):
		return BANT(i2h(int(self) ** int(other)))
	def __xor__(self, other):
		return BANT(xor_strings(self.this.str(), other.this.str()))
		
	def __str__(self):
		return ''.join([chr(i) for i in self.this])
	def __repr__(self):
		return "BANT(\"" + self.hex() + "\", True)"
	def __int__(self):
		return sum( [self.this[::-1][i] * (2 ** (i * 8)) for i in range(len(self.this))] )
	def __float__(self):
		return float(self.__int__())
		
	def __hash__(self):
		return int(self)
	
	def encode(self, f='bant'):
		if f == 'bant': return ENCODEBANT(self)
		elif f == 'hex': return self.hex()
	def to_json(self):
		return self.encode()
	
	def hex(self):
		return self.str().encode('hex')
	def concat(self, other):
		return BANT(self.this + other.this)
	def raw(self):
		return self.this
	def str(self):
		return self.__str__()
	def int(self):
		return self.__int__()
	def increment(self, by=1):
		return BANT(i2h(int(self) + 1))
		
		

def DECODEBANT(b58s):
	return BANT(b58decode(b58s))
def ENCODEBANT(b):
	return b58encode(b.str())
	


		
class HashTree:
	def __init__(self, *init):
		if len(init) == 0: self.leaves = []
		self.leaves = [HashTree(BANT(i, fromHex=False)) for i in init]
		self.myhash = BANT('00')
		self.recalcHash()
		
		
	def doHash(self, msg):
		return BANT(hashlib.sha256(str(msg)).digest(), fromHex=False)
		
		
	def hashRow(self, row):
		''' Take a row and create a row of half the length '''
		if len(row) == 0: return BANT('')
		if len(row) == 1: return row[:]
		i = 0
		rt = []
		if len(row) % 2 == 1: row = row[:] + [row[-1]]
		for i in range(len(row)/2): rt.append(self.doHash(row[2*i].concat(row[2*i+1])))
		return rt
		
		
	def recalcHash(self):
		rt = self.leaves[:]
		if len(self.leaves) == 0: 
			rt = [BANT('00')]
		while len(rt) > 1:
			print rt
			rt = self.hashRow(rt)
		self.myhash = rt[0]
		return True
		
	
	def add(self, h, v=BANT('00')):
		self.leaves.append(BANT(h))
		self.recalcHash()
		
	def remove(self, h):
		if h not in self.leaves:
			return False
		else:
			h.remove(h)
			self.recalcHash()
			return True
			
	def getHash(self):
		return self.myhash
		
	def __str__(self):
		return str(self.myhash)
		
		
		
class Forest(object):
	''' Holds many trees '''
	def __init__(self):
		self.trees = set()
		
	def add(self, tree):
		assert isinstance(tree, Hashtree)
		self.trees.add(tree)
		
	def remove(self, tree):
		self.trees.remove(tree)
	
		
class GPDHTChain(Forest):
	''' Holds a PoW chain and can answer queries '''
	def __init__(self, genesisheader=None):
		super(GPDHTChain, self).__init__()
		
		self.decs = {}
		self.hashfunc = hashfunc
		if genesisheader != None: self.setGenesis(genesisheader)
		else: self.setGenesis([])
		self.head = self.genesishash
		
		self.headerMap = {
			"version": 0,
			"prevblock": 1,
			"uncles": 2,
			"target": 3,
		}
	
	
	def hash(self, message):
		return BANT(sha256(str(message)).digest())
		
		
	def setGenesis(self, genesisheader):
		assert int(genesisheader[self.headerMap["uncles"]]) == 0
		assert int(genesisheader[self.headerMap["prevblock"]]) == 0
		assert int(genesisheader[self.headerMap["version"]]) == 0
		
		genesishash = 0
		self.target = unpackTarget(genesisheader[self.headerMap["target"]])
		print "%064x" % self.target
		assert int(genesishash) < self.target
		
		self.genesisheader = genesisheader
		self.genesishash = genesishash
		
	
	def addBlock(self, block, *items):
		assert len(items) == 1 # items should be a list of a singular metadata item
		blockinfo = items[0]
		h = self.hash(''.join(str(i) for i in blockinfo))
		
	
	
	def validAlert(self, alert):
		# TODO : return True if valid alert
		pass
		
	
	def getSuccessors(self, blocks, stop):
		# TODO : find HCB and then some successors until stop or max num
		pass
		
		
	def getTopBlock(self):
		return self.head
		
		
class Node:
	''' Simple class to hold node info '''
	def __init__(self, ip, port):
		self.ip = ip
		self.port = port
		self.versionInfo = None
		self.alive = False
		self.testAlive()
	def sendMessage(self, msg):
		pass
	def testAlive(self):
		# TODO : request /about from node, true if recieved
		self.alive = True
		
