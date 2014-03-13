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
		elif isinstance(initString, BANT):
			self.this = initString.this[:]
		else:
			self.this = bytearray(bytes(initString))
			
		while padTo - len(self.this) > 0: self.this = bytearray([0]) + self.this
			
		self.isBANT = True
	
		
	def __lt__(self, other):
		return int(self) < int(other)
	def __gt__(self, other):
		return int(self) > int(other)
	def __eq__(self, other):
		if other == None: return False
		if isinstance(other, str):
			return self.this == other
		return int(self) == int(other)
	def __ne__(self, other):
		return not (self == other)
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
	
	def getHash(self):
		return hashfunc(self)
	
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
		
		

def DECODEBANT(s):
	return BANT(s.decode('hex'))
	#return BANT(b58decode(b58s))
def ENCODEBANT(b):
	return b.hex()
	#return b58encode(b.str())
	


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
			


#==============================================================================
# JSON OPERATIONS
#==============================================================================	
	
	
def json_str_to_bant(obj):
	print 'json_str_to_bant - %s' % str(obj)
	if isinstance(obj, str):
		return BANT(obj.decode('hex'))
	if isinstance(obj, unicode):
		return BANT(str(obj).decode('hex'))
	if isinstance(obj, list):
		rt = []
		for a in obj: rt.append(json_str_to_bant(a))
		return rt
	if isinstance(obj, dict):
		rt = {}
		for k,v in obj.iteritems():
			rt[json_str_to_bant(k)] = json_str_to_bant(v)
	return obj
	
def json_loads(obj):
	a = json.loads(obj)
	return json_str_to_bant(a)
	



#==============================================================================
# HashTree
#==============================================================================
		
class HashNode:
	def __init__(self, ttl, children):
		self.myhash = None
		self.parent = None
		self.children = children
		if isinstance(children[0], HashNode):
			if len(children) == 1: self.children += children
			self.ttl = children[0].ttl
			assert children[0].ttl == children[1].ttl
		elif len(children) < 1 or len(children) > 2: raise ValueError("HashNode: children must be a list/tuple of length 1 or 2")
		else: self.ttl = ttl
		self.getHash()
		if not isinstance(children[0], BANT):
			_ = [self.children[0].setParent(self), self.children[1].setParent(self)]
		
	def getHash(self, force=False):
		if self.myhash == None or force:
			# p0.hash ++ ttl ++ p1.hash
			tripconcathash = lambda x: hashfunc(self.children[x[0]].getHash().concat(BANT(self.ttl).concat(self.children[x[1]].getHash())))
			if len(self.children) == 1: self.myhash = tripconcathash([0,0])
			else: self.myhash = tripconcathash([0,1])
			if self.parent != None: self.parent.getHash(True)
		return self.myhash
		
	def getChild(self, lr):
		return self.children[lr]
		
	def setChild(self, lr, newchild):
		self.child[lr] = newchild
		self.getHash(True)
		
	def setParent(self, parent):
		self.parent = parent
		
		
class HashTree:
	def __init__(self, init, hashFirst=False):		
		assert len(init) > 0
		
		if hashFirst: 
			leaves = [self.doHash(BANT(i)) for i in init]
		else:
			if False in [len(i) == 32 for i in init]: raise ValueError("HashTree: if hashFirst=False then initialization leaves must all be 32 bytes")
			leaves = init
		
		chunks = leaves
		ttl = 0
		while len(chunks) > 1:
			newChunks = []
			for i in xrange(0,len(chunks),2):
				newChunks.append(HashNode(ttl, leaves[i:i+2]))
			chunks = newChunks
			ttl += 1
		self.root = chunks[0]
		self.height = ttl
		
		
	def doHash(self, msg):
		return hashfunc(msg)
		
		
	def rightmost(self, ttl):
		w = self.root 
		while True:
			if w.ttl == ttl: return w
			if w.ttl <= 0: raise ValueError("HashTree.rightmost: ttl provided is outside bounds")
			w = w.children[1]
		
	
	def append(self, v=BANT('00')):			
		n = self.n-1
		ttl = 0
		a = HashNode(ttl, [v])
		while True:
			if n % 2 == 1:
				b = HashNode(ttl+1, [self.rightmost(ttl), a])
				if b.ttl > self.root.ttl: self.root = b
				else: self.rightmost(ttl+1).setChild(1, b)
				break
			else:
				ttl += 1
				a = HashNode(ttl, [a])
				n /= 2
		self.n += 1
		
		
	def remove(self, h):
		pass
		if h not in self.leaves:
			return False
		else:
			self.leaves.remove(h)
			self.recalcHash()
			return True
			
			
	def update(self, pos, val):
		pass
		if int(pos) >= len(self.leaves): raise ValueError("HashTree.update: 'pos' out of range.")
		self.leaves[pos] = val[:]
		self.recalcHash() # todo : make not terrible
		
		
			
	def getHash(self):
		return self.root.getHash()
		
	def __str__(self):
		return str(self.myhash)
	
	def __hash__(self):
		return int(self.getHash())
		
	def __eq__(self, other):
		if isinstance(other, str):
			return self.getHash().str() == other
		elif isinstance(other, BANT):
			return self.getHash() == other
		else:
			return self.getHash() == other.getHash()
		
		

#==============================================================================
# Forests, Chains, Etc
#==============================================================================
				
		
		
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
		h = HashTree(potentialTree, hashFirst=True)
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
			BANT(b'\xff\xff\xff\x01'),
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
		print 'addBlock: block.leaves:', block.leaves
		if self.initComplete == False:
			assert blockInfo[self.headerMap['prevblock']] == BANT(bytearray(32))
		else:
			print 'addBlock: repr(prevblock):', repr(blockInfo[self.headerMap['prevblock']])
			assert blockInfo[self.headerMap['prevblock']] in self.trees
		h = self.hashBlockInfo(blockInfo)
		assert h in block.leaves
		print 'addBlock: NEW BLOCK', block.getHash().hex()
		self.trees.add(block)
		
		if self.initComplete == False:
			self.initComplete = True
			
		# TODO : fire block to other nodes
			
		return True
		
		
	
	
	def validAlert(self, alert):
		# TODO : return True if valid alert
		pass
		
	
	def getSuccessors(self, blocks, stop):
		# TODO : find HCB and then some successors until stop or max num
		pass
		
		
	def getTopBlock(self):
		return self.head
		
	
	def learnOfDB(self, db):
		self.db = db
		self.loadChain()
		
		
		

#==============================================================================
# Node
#==============================================================================
		
		
class Node:
	''' Simple class to hold node info '''
	def __init__(self, ip, port):
		self.ip = ip
		self.port = port
		self.versionInfo = None
		self.alive = False
		self.score = 0
		self.testAlive()
		
		self.about = None
		
	def sendMessage(self, path, msg, method="GET"):
		fireHTTP(self, path, msg, method)
		
	def testAlive(self):
		# TODO : request /about from node, true if recieved
		self.alive = True
		



#==============================================================================
# Network Specific - Value Laden Data Structures
#==============================================================================
		

class Block:
	def __init__(hashtree):
		pass
		

	
#==============================================================================
# Constants
#==============================================================================
		

z32 = BANT('',padTo=32)
