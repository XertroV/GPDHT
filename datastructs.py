import time

from hashlib import sha256
from utilities import *

from bitcoin.base58 import encode as b58encode, decode as b58decode


def hashfunc(msg):
	return BANT(sha256(str(msg)).digest())

eba = bytearray('')
def ADDBYTEARRAYS(a,b,carry=0):
	if (a == eba or b == eba) and carry == 0: return a + b
	if a == eba and b == eba and carry == 1: return bytearray([carry])
	for x,y in [(a,b),(b,a)]:
		if x == eba: return ADDBYTEARRAYS(y[:-1]+bytearray([0]), ADDBYTEARRAYS(bytearray([y[-1]]), bytearray([carry])))
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
	def __init__(self, initString=b'\x00', fromHex=False, padTo=0):
		if fromHex == True:
			'''input should be a string in hex encoding'''
			self.this = bytearray(initString.decode('hex')) # byte array
		elif isinstance(initString, int):
			self.this = BANT(i2s(initString)).this
		else:
			self.this = bytearray(bytes(initString))
			
		while padTo - len(self.this) > 0: self.this = bytearray([0]) + self.this
			
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
		return BANT(int(self) - int(other))
		
	def __len__(self):
		return len(self.this)
	def __getitem__(self,key):
		return BANT(self.this[key])
	def __setitem__(self,key,value):
		self.this[key] = value
		
	# do I need to do the r___ corresponding functions? (__radd__ for example)
	def __add__(self, other):
		return BANT(ADDBYTEARRAYS(self.this, BANT(other).this))
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
		
		

def DECODEBANT(b58s):
	return BANT(b58decode(b58s))
def ENCODEBANT(b):
	return b58encode(b.str())
	


#==============================================================================
# RLP OPERATIONS
#==============================================================================
	
def RLP_WRAP_DESERIALIZE(rlpIn):
	if rlpIn.raw()[0] >= 0xc0:
		if rlpIn.raw()[0] > 0xf7:
			sublenlen = rlpIn.raw()[0] - 0xf7
			sublen = rlpIn[1:sublenlen+1].int()
			msg = rlpIn[sublenlen+1:sublenlen+sublen+1]
			rem = rlpIn[sublenlen+sublen+1:]
		
		else:
			sublen = rlpIn.raw()[0] - 0xc0
			msg = rlpIn[1:sublen+1]
			rem = rlpIn[sublen+1:]
			
		o = []
		while len(msg) > 0:
			t, msg = RLP_WRAP_DESERIALIZE(msg)
			o.append(t)
		return o, rem
	
	elif rlpIn.raw()[0] > 0xb7:
		subsublen = rlpIn.raw()[0] - 0xb7
		sublen = rlpIn[1:subsublen+1].int()
		msg = rlpIn[subsublen+1:subsublen+sublen+1]
		rem = rlpIn[subsublen+sublen+1:]
		return msg, rem
		
	elif rlpIn.raw()[0] >= 0x80:
		sublen = rlpIn.raw()[0] - 0x80
		msg = rlpIn[1:sublen+1]
		rem = rlpIn[sublen+1:]
		return msg, rem
	
	else:
		return rlpIn[0], rlpIn[1:]
		
def RLP_DESERIALIZE(rlpIn):
	if not isinstance(rlpIn, BANT): raise ValueError("RLP_DESERIALIZE requires a BANT as input")
	if rlpIn == BANT(''): raise ValueError("RLP_DESERIALIZE: Requires nonempty BANT")
	
	ret, rem = RLP_WRAP_DESERIALIZE(rlpIn)
	if rem != BANT(''): raise ValueError("RLP_DESERIALIZE: Fail, remainder present")
	return ret
	
def RLP_ENCODE_LEN(b, islist = False):
		if len(b) == 1 and not islist and b < 0x80:
			return bytearray([])
		elif len(b) < 56:
			if not islist: return bytearray([0x80+len(b)])
			return bytearray([0xc0+len(b)]) 
		else:
			if not islist: return bytearray([0xb7+len(i2s(len(b)))]) + bytearray(i2s(len(b)))
			return bytearray([0xf7+len(i2s(len(b)))]) + bytearray(i2s(len(b)))
	
def RLP_SERIALIZE(blistIn):
	rt = bytearray('')
	
	if isinstance(blistIn, BANT):
		rt.extend(RLP_ENCODE_LEN(blistIn) + blistIn.raw())
		ret = rt
	elif isinstance(blistIn, list):
		for b in blistIn:
			rt.extend( RLP_SERIALIZE(b).raw() )
		
		ret = RLP_ENCODE_LEN(rt, True)
		ret.extend(rt)
	
	return BANT(ret)
			
	
	
	

		
class HashTree:
	def __init__(self, init):
		if len(init) == 0: self.leaves = []
		self.leaves = [self.doHash(BANT(i)) for i in init]
		self.myhash = BANT('00')
		self.recalcHash()
		
		
	def doHash(self, msg):
		return hashfunc(msg)
		
		
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
			self.leaves.remove(h)
			self.recalcHash()
			return True
			
			
	def update(self, pos, val):
		if int(pos) >= len(self.leaves): raise ValueError("HashTree.update: 'pos' out of range.")
		self.leaves[pos] = val[:]
		self.recalcHash() # todo : make not terrible
		
		
			
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
		self.initComplete = False
		self.head = BANT(chr(0))
		
		self.headerMap = {
			"version": 0,
			"prevblock": 1,
			"uncles": 2,
			"target": 3,
			"timestamp":4,
		}
		
		self.decs = {}
		self.hashfunc = hashfunc
		if genesisheader != None: self.setGenesis(genesisheader)
		else: self.setGenesis(self.mine(self.blockInfoTemplate()))
		
		
	def mine(self, blockInfoTemplate):
		blockInfoHash = self.hashBlockInfo(blockInfoTemplate)
		blockInfoRLP = RLP_SERIALIZE(blockInfoTemplate)
		target = unpackTarget(blockInfoTemplate[self.headerMap['target']])
		message = "It was a bright cold day in April, and the clocks were striking thirteen."
		nonce = self.hash(message)
		potentialTree = [blockInfoRLP, blockInfoRLP, message, nonce]
		h = HashTree(potentialTree)
		count = 0
		while True:
			count += 1
			h.update(3, nonce)
			PoW = h.getHash()
			if PoW < target:
				break
			nonce += 1
			if count % 10000 == 0:
				print count, PoW.hex()
		print 'Chain.mine: Found Soln : %s', PoW.hex()
		return (h, blockInfoTemplate)
		
	
	def blockInfoTemplate(self):
		return [
			BANT(b'\x00\x01'),
			BANT(bytearray(32)),
			BANT(bytearray(32)),
			BANT(b'\xff\xff\xff\x02'),
			BANT(int(time.time()), padTo=6),
			BANT('', padTo=4)
		]
			
	
	
	def hash(self, message):
		return hashfunc(message)
		
	def hashBlockInfo(self, blockInfo):
		return self.hash(RLP_SERIALIZE(blockInfo))
		
		
	def setGenesis(self, bPair):
		tree, blockInfo = bPair
		print 'Setting Genesis Block'
		assert int(blockInfo[self.headerMap["uncles"]]) == 0
		assert int(blockInfo[self.headerMap["prevblock"]]) == 0
		assert int(blockInfo[self.headerMap["version"]]) == 1
		
		self.target = unpackTarget(blockInfo[self.headerMap["target"]])
		print "Chain.setGenesis: target : %064x" % self.target
		assert int(tree.getHash()) < self.target
		
		self.genesisInfo = blockInfo
		self.genesisTree = tree
		self.genesisHash = tree.getHash()
		
		self.head = self.genesisTree.getHash()
		
		self.addBlock(tree, blockInfo)
		
	
	def addBlock(self, block, blockInfo):
		print 'addBlock: Potential block', block.getHash().hex()
		print block.leaves, self.initComplete
		if self.initComplete == False:
			assert blockInfo[self.headerMap['prevblock']] == BANT(bytearray(32))
		else:
			assert blockInfo[self.headerMap['prevblock']] in self.trees
		h = self.hashBlockInfo(blockInfo)
		assert h in block.leaves
		print 'addBlock: NEW BLOCK', block.getHash().hex()
		
		if self.initComplete == False:
			self.initComplete = True
		
		
	
	
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
		
