#!/usr/bin/python

''' Author: Max Kaye 
About: Gracht is the reference implementation of GPDHT.
License: Undecided '''


#==============================================================================
# INIT CONFIG and DS
#==============================================================================


from datastructs import *

# config
logfilename = 'log_gracht'

dbPre = 'gracht'
dbnum = 2

hostport = 32555
bindto = '0.0.0.0'
aboutInfo = {
	"version":"gracht/0.0.1",
	"port":str(hostport),
}


#==============================================================================
# IMPORTS
#==============================================================================


# import and init
from flask import Flask
from flask import request, render_template, redirect, abort
app = Flask(__name__)
from werkzeug.routing import BaseConverter
class BantConverter(BaseConverter):
	def __init__(self, url_map, *items):
		super(BantConverter, self).__init__(url_map)
	def to_python(self, value):
		return DECODEBANT(value)
	def to_url(self, value):
		return DECODEBANT(value)
app.url_map.converters['bant'] = BantConverter

import logging
log_handler = logging.FileHandler(logfilename)
log_handler.setLevel(logging.WARNING)
app.logger.addHandler(log_handler)

from hashlib import sha256
from binascii import hexlify
import json, math



#==============================================================================
# NETWORK
#==============================================================================


class GPDHTDatabase:
	def __init__(self):
		import redis
		self.r = redis.StrictRedis(host='localhost', port=6379, db=dbnum)
		self.dbPre = dbPre
		
	def __pp(self, rt):
		if rt == None: return BANT(chr(0))
		else: return rt	
		
	def path(self, p):
		return '%s:%s' % (self.dbPre, str(p))
		
	def exists(self,toTest):
		return self.r.exists(self.path(toTest))
	def set(self,toSet,value):
		return self.r.set(self.path(toSet),value)
	#def get(self,toGet):
	#	return self.r.get(self.pattoGet))
	def rpush(self, toPush, value):
		return self.r.rpush(self.path(toPush), value)
	def lrange(self, key, a, b):
		return self.__pp(self.r.lrange(self.path(key), int(a), int(b)))
	
	# read (higher)
	
	def getEntry(self, toGet):
		return ALL_BANT(self.lrange(toGet,0,-1))
		
	def getSuccessors(self, blockhash):
		s = []
		t = 0
		print 'getSuccessors:', repr(blockhash)
		while self.exists(blockhash + BANT(2**t)):
			s.append(self.getEntry(blockhash + BANT(2**t)))
			t += 1
		print 'getSuccessors:', ALL_BANT(s)
		return ALL_BANT(s)
		
	def getAncestors(self, blockhash):
		a = []
		t = 0
		while self.exists(blockhash - BANT(2**t)):
			a.append(self.getEntry(blockhash - BANT(2**t)))
			t += 1
		return ALL_BANT(a)
	
	# write (higher level)
	
	def setEntry(self, toSet, stuff):
		self.r.delete(self.path(toSet))
		self.r.rpush(self.path(toSet), *stuff)
	
	def linkAnc(self, young, old, diff):
		self.rpush(young - diff, old)
		self.rpush(old + diff, young)
	
	def setAncestors(self, block, prevblockhash):
		s = 0
		h = block.getHash()
		cur = prevblockhash
		if cur == 0: return True # genesis block
		self.linkAnc(h, cur, 2**s)
		while self.exists(cur - 2**s):
			cur = self.getEntry(cur - 2**s)[0]
			s += 1
			self.linkAnc(h, cur, 2**s)
		
	
	def dumpList(self, l, h=None):
		print 'dumpList', repr(h), repr(l)
		if h == None:
			h = hashfunc(RLP_SERIALIZE(l))
		p = self.r.pipeline()
		p.delete(self.path(h))
		p.rpush(self.path(h), *l)
		p.execute()
	
	def dumpTree(self, tree):
		self.dumpList(tree.leaves(), tree.getHash())
			
	

#==============================================================================
# ROUTES / MESSAGES
#==============================================================================

		

@app.route("/about",methods=["POST"])	
def about():
	return json.dumps(aboutInfo)
	
@app.route("/list",methods=["POST"])
def list():
	return json.dumps(subscribedTo)
	
@app.route("/friends",methods=["POST"])
def friends():
	return json.dumps(knownNodes)
	
@app.route("/alerts",methods=["POST"])
def alerts():
	return json.dumps(knownAlerts)
	
@app.route("/<bant:chain>/topblock",methods=["POST"])
def getTopBlock(chain):
	return json.dumps([chains[chain].getTopBlock()])
	
@app.route("/<bant:chain>/newblock",methods=["POST"])
def learnNewBlock(chain):
	print '/newblock - hashtree leaves:', repr(json_loads(request.form['hashtree']))
	hashtree = HashTree(json_loads(request.form['hashtree']))
	blockinfo = json_loads(request.form['blockinfo'])
	print '/newblock - hashtree: %s, blockinfo: %s' % (repr(hashtree.leaves), repr(blockinfo))
	added = chains[chain].addBlock(hashtree, blockinfo)
	if added == True:
		for n in knownNodes[chain]:
			print repr(n)
			n.sendMessage('/newblock', {'hashtree':hashtree.leaves(), 'blockinfo':blockinfo})
		return json.dumps({'error':''})
	return json.dumps({'error':added})
	
@app.route("/<bant:chain>/gettrees",methods=["POST"])
def getTrees(chain):
	roots = json_loads(request.form['roots'])
	trees = []
	for root in roots:
		trees.append(db.getTreeFromRoot(root))
	return json.dumps(trees)
	
@app.route("/<bant:chain>/successors",methods=["POST"])
def getSuccessors(chain):
	print './successors, blocklocator:', repr(request.form['blocklocator'])
	blocklocator = json_loads(request.form['blocklocator'])
	blocks = blocklocator['blocks']
	if 'stop' in blocklocator: stop = blocklocator['stop']
	else: stop = ''
	print './successors:',repr(blocks)
	successors = chains[chain].getSuccessors(blocks, stop)
	return json.dumps({'error':'', 'successors':successors})
	
@app.route("/<bant:chain>/alerts",methods=["POST"])
def getChainAlerts(chain):
	return json.dumps(knownAlerts[chain])
	
@app.route("/<bant:chain>/alert",methods=["POST"])
def newAlert(chain):
	alert = json_loads(request.form['alert'])
	if not chains[chain].validAlert(alert): return json.dumps({'error':'invalid alert'})
	knownAlerts[chain].append(alert)
	db.recordAlert(chain, alert)
	return json.dumps({'error':''})
	
@app.route("/<bant:chain>/getbranch",methods=["POST"])
def getBranch(chain):
	merkleroot = json_loads(request.form['merkleroot'])
	leaf = json_loads(request.form['leaf'])
	branch = db.getBranchFromRoot(merkleroot, leaf)
	return json.dumps({'error':'', 'branch':branch})
	
@app.route("/<bant:chain>/getentries",methods=["POST"])
def getEntries(chain):
	print 'getEntries:',request.form['entries']
	entries = json_loads(request.form['entries'])
	response = []
	for entryHash in entries:
		response.append( db.getEntry(entryHash) )
	print 'getEntries:',response
	return json.dumps(response)
	
@app.route("/<bant:chain>/subscribe",methods=["POST"])
def subscribeNode(chain):
	# if chain not in chains: abort(404)
	print '/subscribe: chain:', repr(chain)
	knownNodes[chain].add(Node(request.remote_addr, int(request.form['port'])))
	print '/%s/subscribe: updated knownNodes with %s:%d' % (chain.hex(), request.remote_addr, int(request.form['port']))
	return json.dumps({'error':''})
	
	

db = GPDHTDatabase()

# GPDHT config
MainChain = GPDHTChain(db=db)
chains = {MainChain.genesisHash : MainChain} # k: genesis block, v: Chain object
subscribedTo = chains.keys() # list of genesis blocks
knownNodes = dict(zip([x for x in subscribedTo],[set() for _ in subscribedTo])) # list of node objects
knownAlerts = dict(zip([x for x in subscribedTo],[set() for _ in subscribedTo])) # list of known alerts



if __name__ == "__main__":
	app.run(host=bindto, port=hostport)
