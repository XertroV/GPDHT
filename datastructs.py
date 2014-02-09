
class ContractStorage:
	def __init__(self):
		# storage is technically not a dictionary but an array
		# A dictionary is used here for simplicity
		self._storage = {}
	def __getitem__(self,key):
		#if type(key) is not int:
		#	key = int(key)
		try:
			return self._storage[key]
		except:
			return 0
	def __setitem__(self, key, val):
		#if type(key) is not int:
		#	key = int(key)
		self._storage[key] = val
	def slice(self, start, end):
		# start inclusive, end exclusive
		ret = []
		while start < end:
			ret.append(self._storage[start])
			start += 1
		return ret
	def printState(self):
		pp.pprint(self._storage)
		