from datastructs import BANT
import hashlib

class HashTree:
	def __init__(self, *init):
		if len(init) == 0: self.leaves = []
		self.leaves = [HashTree(BANT(i, fromHex=False)) for i in init]
		self.myhash = BANT('00')
		self.recalcHash()
		
		
	def doHash(self, msg):
		return BANT(hashlib.sha256(str(msg)).digest(), fromHex=False, len=30)
		
		
	def hashRow(self, row):
		if len(row) == 0: return BANT('')
		if len(row) == 1: return row[:]
		i = 0
		if len(row) % 2 == 1:
			row = row[:] + [row[-1]]
		rt = []
		while i < len(row):
			rt.append(self.doHash(row[i].concat(row[i+1])))
			i += 2
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
			


class Block:
	def __init__(self):
		pass


if __name__ == "__main__":
	h = HashTree('1','2','3','4')
	print h.getHash().hex()
	
	
	
	
	
	
