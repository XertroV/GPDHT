#!/usr/bin/python

''' Author: Max Kaye 
About: Gracht is the reference implementation of GPDHT over HTTP.
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



# GPDHT config
MainChain = GPDHTChain()
chains = {MainChain.genesisHash : MainChain} # k: genesis block, v: Chain object
print chains
subscribedTo = chains.keys() # list of genesis blocks
knownNodes = dict(zip([x.encode() for x in subscribedTo],[[] for _ in subscribedTo])) # list of node objects
knownAlerts = dict(zip([x.encode() for x in subscribedTo],[[] for _ in subscribedTo])) # list of known alerts



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
import json
from bitcoin.base58 import encode as b58encode, decode as b58decode


#==============================================================================
# NETWORK
#==============================================================================


class Database:
	def __init__(self):
		import redis
		self.r = redis.StrictRedis(host='localhost', port=6379, db=dbnum)
		self.dbPre = dbPre
	def exists(self,toTest):
		return self.r.exists('%s:%s' % (self.dbPre,toTest))
	def set(self,toSet,value):
		return self.r.set('%s:%s' % (self.dbPre,toSet),value)
	def get(self,toGet):
		return self.r.get('%s:%s' % (self.dbPre,toGet))
	def rpush(self,toPush, value):
		return self.r.rpush('%s:%s' % (self.dbPre,toPush), value)


#==============================================================================
# ROUTES / MESSAGES
#==============================================================================

		

@app.route("/about")	
def about():
	return json.dumps(aboutInfo)
	
@app.route("/list")
def list():
	return json.dumps(subscribedTo)
	
@app.route("/friends")
def friends():
	return json.dumps(knownNodes)
	
@app.route("/alerts")
def alerts():
	return json.dumps(knownAlerts)
	
@app.route("/<bant:chain>/topblock",methods=["GET"])
def getTopBlock(chain):
	print repr(chain)
	return json.dumps([chains[chain].getTopBlock()])
	
@app.route("/<bant:chain>/newblock",methods=["POST"])
def putNewBlock(chain):
	hashtree = json.loads(request.form['hashtree'])
	blockinfo = json.loads(request.form['blockinfo'])
	return chains[chain].addBlock(hashtree, blockinfo)
	
@app.route("/<bant:chain>/gettrees",methods=["POST"])
def getTrees(chain):
	roots = json.loads(request.form['roots'])
	trees = []
	for root in roots:
		trees.append(db.getTreeFromRoot(root))
	return json.dumps(trees)
	
@app.route("/<bant:chain>/sucessors",methods=["POST"])
def getSuccessors(chain):
	blocklocator = json.loads(request.form['blocklocator'])
	blocks = blocklocator['blocks']
	if 'stop' in blocklocator: stop = blocklocator['stop']
	else: stop = ''
	return chains[chain].getSuccessors(blocks, stop)
	
@app.route("/<bant:chain>/alerts",methods=["GET"])
def getChainAlerts(chain):
	return json.dumps(knownAlerts[chain])
	
@app.route("/<bant:chain>/alert",methods=["POST"])
def newAlert(chain):
	alert = json.loads(request.form['alert'])
	if not chains[chain].validAlert(alert): return json.dumps({'error':'invalid alert'})
	knownAlerts[chain].append(alert)
	db.recordAlert(chain, alert)
	return json.dumps({'error':''})
	
@app.route("/<bant:chain>/getbranch/<bant:MR>/<bant:leaf>",methods=["GET"])
def getBranch(chain, MR, leaf):
	pass
	
@app.route("/<bant:chain>/getentry",methods=["POST"])
def getEntrys(chain):
	entries = json.loads(request.form['entries'])
	response = []
	for entryHash in entries:
		response.append( db.getEntry(entryHash) )
	return json.dumps(response)
	
@app.route("/<bant:chain>/subscribe",methods=["POST"])
def subscribeNode(chain):
	# if chain not in chains: abort(404)
	nodes[chain].add(Node(request.remote_addr, int(request.form['port'])))
	return json.dumps({'error':''})
	
	

if __name__ == "__main__":
	db = Database()
	app.run(host=bindto, port=hostport)
