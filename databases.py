class Database:
	''' Defines the structure of the database. Every DB implementation
	must support these methods. '''
	
	def set(self, key, value): pass
	def lpush(self, key, *values): pass
	def rpush(self, key, *values): pass
	def get(self, key): pass
	def delete(self, key): pass
	def exists(self, key): pass
	
	def pipeline(self): pass
	
class Redis(Database):
	def __init__(self, host="127.0.0.1", port=6379, db=15):
		import redis
		self.r = redis.StrictRedis(host, port, db)
		
	def __postprocess(self, rt):
		if rt == None: return chr(0)
		else: return rt	
			
	def pipeline(self): return self.r.pipeline()
			
	# write
	def set(self, key, value): return self.r.set(key, str(value))
	
	def lpush(self, key, *values): return self.r.lpush(str(key), *strlist(values))
	def lpushx(self, key, *values): return self.r.lpushx(str(key), *strlist(values))
	def rpush(self, key, *values): return self.r.rpush(str(key), *strlist(values))
	def rpushx(self, key, *values): return self.r.rpushx(str(key), *strlist(values))
	
	def delete(self, key): return self.r.delete(str(key))
	
	# WARNING!
	def flushdb(self): return None # return self.r.flushdb()
	
	# read
	def get(self, key): 
		rt = self.r.get(str(key))
		return self.__postprocess(rt)
	
	def lrange(self, key, start, stop):
		rt = self.r.lrange(str(key), int(start), int(stop))
		return self.__postprocess(rt)
		
	def exists(self, key):
		return self.r.exists(str(key))
		
	def sismember(self, key, member):
		return self.r.sismember(str(key), str(member))
		
	def llen(self, key):
		return self.__postprocess(self.r.llen(str(key)))
		
	def lindex(self, key, index):
		return self.__postprocess(self.r.lindex(str(key), int(index)))
		
		
