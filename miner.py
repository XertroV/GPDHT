from utilities import *
from datastructs import *

import urllib, json, time

host = "127.0.0.1"
port = 32555
parent = Node(host, port)
chain = ''


def getChain():
    return BANT(json.loads(goGetHTTP(parent, '/list'))[0].decode('hex'))

def getTopBlock():
    return BANT(json.loads(goGetHTTP(parent, '/%s/topblock' % chain.encode('hex')))[0].decode('hex'))

def mine(blockInfoTemplate):
	blockInfoRLP = RLP_SERIALIZE(blockInfoTemplate)
	target = unpackTarget(blockInfoTemplate[3])
	message = BANT("It was a bright cold day in April, and the clocks were striking thirteen.")
	nonce = hashfunc(message)
	potentialTree = [chain, hashfunc(blockInfoRLP), hashfunc(message), nonce]
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
	print 'mine: Found Soln : %s', PoW.hex()
	return (h, blockInfoTemplate)
	
def push(pair):
    tree, blockInfo = pair
    print 'push - tree.leaves :', json.dumps(tree.leaves)
    return json.loads(goGetHTTP(parent, '/%s/newblock' % chain.encode('hex'), payload={'hashtree':json.dumps(tree.leaves), 'blockinfo':json.dumps(blockInfo)}, method="POST"))
    
def miner():
    blockInfo = [
	BANT(b'\x00\x01'),
	getTopBlock(),
	BANT(bytearray(32)),
	BANT(b'\xff\xff\xff\x01'),
	BANT(int(time.time()), padTo=6),
	BANT('', padTo=4)
    ]
    pair = mine(blockInfo)
    print push(pair)
    print pair

chain = getChain()
print 'Miner: Chain: %s' % chain.hex()
miner()
