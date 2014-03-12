#!/usr/bin/python

from datastructs import *
from hashlib import sha256

from btpeer import *
from utilities import *
import sys, threading, time, traceback, argparse

from databases import Redis

'''
The PoWPRISM listens for messages relating to particular PoW Chains and 
acts on those messages based on rules defined in the class.

Like a PRISM, PoWPRISM takes incoming messages and sends them to many
new locations.

Typically a PP will:

listen for - PoW Declarations
				- Validate the declaration header (PoW and otherwise)
				- custom rules?
				- Record the PD @ it's hash
				- Append PD Hash to index
		   - Single Declarations
				- Validate SD
				- Custom rules?
'''

# networking commands
VERSION = "VERS"; INFO = "INFO"; FRIENDS = "FRND"; DESCRIBE = "DESC"
DISPUTED = "DISP"; CHAIN = "DCHN"

# metadata shouldn't be included at this level
# PDs in the db
PD = 0; INDEX = 1; HEIGHT = 2; CUMDIFF = 3; HISTORY = 4

ZERO = chr(0)


class PoWPRISM(BTPeer):
	''' PowPRISM is a generic class meant to provide the base, universal 
	logic for the underlying GPDHT. It should not know about state logic '''
	def __init__(self, maxpeers, serverport):
		
		# is this a crime against humanity?
		self.__processPD = None
		self.__processSD = None
		
				
			
			
# simplest case; only accept PDs
class TestNet1(PoWPRISM):
	def __init__(self, maxpeers, serverport, db=15):
		BTPeer.__init__(self, maxpeers, serverport)
		
		self.addrouter(self.__router)
		
		self.debug = True
		
		self.handlers = {
			VERSION: self.__handle_version,
			INFO: self.__handle_info,
			FRIENDS: self.__handle_friends,
			DESCRIBE: self.__handle_describe,
			DISPUTED: self.__handle_disputed,
			CHAIN: self.__handle_chain,
		}
		for a in self.handlers:
			self.addhandler(a, self.handlers[a])
		
		PoWPRISM.__init__(self, maxpeers, serverport)
		self.__loadInitialVariables()
				
		self.chain = Chain()
		self.genesisheaderlist = [
			'00000001'.decode('hex'),
			'0000000000000000000000000000000000000000000000000000000000000000'.decode('hex'),
			'87c6eea9ad933605ea59565c77efc446eeba0aa83537d6bd79305b1fa8292639'.decode('hex'),
			'0fffff02'.decode('hex'),
			'00000000'.decode('hex')
			]
		self.genesisheader = ''.join(self.genesisheaderlist)
		self.chain.setGenesis(self.genesisheader)
		
		self.disputed = {}
		self.banned = set()
		

	def __debug(self, msg):
		if self.debug:
			btdebug(msg)
		
	def __router(self, peerid):
		if peerid not in self.getpeerids():
			return (None,None,None)
		else:
			return [peerid] + list(self.peers[peerid])
		
	def __handle_info(self, peerconn, data):
		if data[0] == ZERO: return self.__processPD(data[1:])
		else: 				return self.__processSD(data[1:])
	def __handle_friends(self, peerconn, data):
		pass
	def __handle_describe(self, peerconn, data):
		pass
	def __handle_disputed(self, peerconn, data):
		pass
	def __handle_chain(self, peerconn, data):
		pass
	def __handle_version(self, peerconn, data):
		pass
		
	def broadcast(self, cmd, msg=""):
		for p in self.peers:
			self.__debug("Broadcast to: %s" % p)
			self.sendtopeer(p,cmd,msg,False)
			
	def buildpeers(self, host, port):
		if self.maxpeersreached():
			return
			
		peerid = None
		
		self.__debug("Building peers from (%s,%s)" % (host,port))
		
		try:
			resp = self.connectandsend(host, port, FRIENDS, '')[0]
			peerid = resp[0]
			
			self.__debug("Contacted %s" % peerid)
			self.__debug(str(resp))
			
			if resp[0] == '':
				return
			
			self.addpeer(peerid, host, port)
		except:
			pass
		
	def __loadInitialVariables(self):
		''' These can be mission critical; should be called very early '''
		self.target1 = 2**256-1
		
		
	def merkleroot(self, hashList):
		merkleroot = self.merkleroot
		lhl = len(hashList)
		if lhl == 1: return hashList
		if lhl % 2 == 1: return merkleroot(hashList + hashList[-1:])
		return merkleroot([self.hash(''.join(hashList[i:i+2])) for i in xrange(0,lhl,2)])
		
		
	def powacceptable(self, pd):
		if long(pd.decode('hex'),16) < self.target: return True
		else: return False
		
	def startminer(self):
		t = threading.Thread( target = self.miner, args = [] )
		t.start()
		
	# miner should really be in the state maker
	def miner(self):
		# get network state to make good blocks
		# DOSTUFFUPDATE()
		
		# construct blockheader
		bhlist = self.genesisheaderlist
		
		while not self.shutdown:
			# update bhlist - set parent to tophash
			while not self.storage.exists(ZERO): time.sleep(0.5)
			hrecentblock = self.storage.lindex(ZERO, -1)
			recentblock = self.storage.lrange(hrecentblock, 0, -1)
			bhlist[1] = self.hash(recentblock[0])
			# also refresh merkle root
			# < stuff >
						
			for _ in xrange(10000):
				pd = ''.join(bhlist)
				hpd = self.hash(pd)
				if long(hpd.encode('hex'),16) < self.target:
					btdebug('Winner: %s' % hpd.encode('hex'))
					btdebug('Parent: %s' % bhlist[1].encode('hex'))
					self.__processPD(pd)
					# zero byte is to mark it as a PD
					self.broadcast(INFO,ZERO+pd)
					
				bhlist[2] = self.hash(bhlist[2])
	# miner should really be in the state maker
	
	
	def __pd_extractVer(self, pd): return pd[:4]
	def __pd_extractPrevHash(self, pd): return pd[4:4+32]
	def __pd_extractMerkleRoot(self, pd): return pd[4+32:4+32+32]
	def __pd_extractPackedTarget(self, pd): return pd[4+32+32:4+32+32+4]
	def __pd_extractVotes(self, pd): return pd[4+32+32+4:4+32+32+4+4]
	
	def __splitPD(self, pd):
		return [pd[:4],pd[4:4+32],pd[4+32:4+32+32],pd[4+32+32:4+32+32+4],pd[4+32+32+4:4+32+32+4+4]]
	
	def __hpd_histIndex(self, hpd): return sumSI(hpd, 2)
	def __hpd_nextIndex(self, hpd): return sumSI(hpd, 1)
	
	
	def hasKey(self, key):
		return self.storage.exists(key)
	
	
	def __processPD(self, pd):
		''' Test a new PD, record if appropriate and return validity '''
		target = unpackTarget(self.__pd_extractPackedTarget(pd))
		hpd = self.hash(pd)
		
		self.__debug("__procPD : Starting")
		self.__debug("__procPD : Parent: %s" % self.__pd_extractPrevHash(pd).encode('hex'))
		
		if long(hpd.encode('hex'),16) >= target: self.__debug("__procPD : hash>=target"); return False
		if target != self.target: self.__debug("__procPD : target-fail"); return False
		if self.hasKey(hpd): self.__debug("__procPD : already-have"); return False
		if not self.hasKey(self.__pd_extractPrevHash(pd)): self.__debug("__procPD : dont-have-parent"); return False
		
		# more checks
		
		# < stuff >
				
		self.__writePD(pd)
		self.__debug("procDB : Finished OKAY")
		return True
		
	def __writePD(self, pd, genesis=False):
		self.__debug("__writePD : Writing %s" % pd.encode('hex'))
		hpd = self.hash(pd)
		
		if genesis:
			genesisdiff = self.target1 / unpackTarget(self.__pd_extractPackedTarget(pd))
			# [ powdec, indexcount, height, cumdiff ]
			pddata = [ pd, ZERO, i2s(1), i2s(genesisdiff) ]
			history = [ hpd ]
		else:
			pddata = [pd]
			
			pddata.append(ZERO)
			
			hparent = self.__pd_extractPrevHash(pd)
			parentdata = self.storage.lrange(hparent, 0, -1)
			parent = parentdata[PD]
			self.storage.rpush(self.__hpd_nextIndex(hparent), hpd)
			
			parentheight = parentdata[HEIGHT]
			height = sumSI(parentheight, 1)
			pddata.append(height)
			
			target = unpackTarget(self.__pd_extractPackedTarget(pd))
			diff = self.target1 / target
			parentdiff = s2i(parentdata[CUMDIFF])
			cumdiff = i2s(parentdiff + diff)
			pddata.append(cumdiff)
			
			history = self.storage.lrange(self.__hpd_histIndex(hparent), 0, -1)
			history.append(hpd)
			j = 2
			hnum = s2i(height)
			while s2i(height) % j == 0:
				history = history[:-2] + [self.hash(history[-2] + history[-1])]
				j *= 2
				
		# add to index
		self.storage.rpush(ZERO, hpd)
		pddata[1] = i2s(self.storage.llen(ZERO) - 1)
		
		# set block deets
		self.storage.delete(hpd)
		self.storage.rpush(hpd, *pddata)
		if self.debug: self.storage.rpush(hpd.encode('hex'), *pddata)
		self.storage.rpush(self.__hpd_histIndex(hpd), *history)
		if self.debug: self.__debug(history)
		self.__debug(self.storage.lrange(hpd,0,-1))
		
		self.__debug("__writePD : Complete")
		
	def __processSD(self, sd):
		pass
		
	def __writeSD(self, sd):
		pass
		
		
			
	def run(self):
		t = threading.Thread( target = self.mainloop, args = [] )
		t.start()
		
		while not self.shutdown:
			try:
				cmd = raw_input("Msg cmd to send > ")
				if cmd not in self.handlers:
					self.__debug("Msg cmd not found.. %s" % cmd)
				else:
					self.broadcast(cmd)
			except KeyboardInterrupt:
				print 'Killing...'
				self.shutdown = True
				break
	


def test():
	#print tn.hash('') == 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'.decode('hex')
	#print tn.merkleroot(['',''])
	
	try:
		if args.miner > 0:
			tn.startminer()
		tn.run()
	except:
		traceback.print_exc()
		tn.shutdown = True
	
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Test GPDHT implementation.')
	parser.add_argument('-miner', nargs=1, type=int, default=0)
	parser.add_argument('-port', nargs=1, type=int, default=1296)
	parser.add_argument('-maxnodes', nargs=1, type=int, default=15)
	args = parser.parse_args()
	# workaround, no clue why this is happening!
	try: args.miner = args.miner[0]
	except: pass
	
	print args
	
	try: args.port = args.port[0]
	except: pass
	port = args.port
	# initial peer
	if port != 1296:
		tn = TestNet1(10, port, db=14)
		tn.storage.flushdb()
		tn.addpeer('192.168.1.9:1296','192.168.1.9',1296)
	else:
		tn = TestNet1(10, port)
	
	test()
