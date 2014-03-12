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
	def set(self, key, value): return self.r.set(key, value)
	
	def lpush(self, key, *values): return self.r.lpush(key, *values)
	def lpushx(self, key, *values): return self.r.lpushx(key, *values)
	def rpush(self, key, *values): return self.r.rpush(key, *values)
	def rpushx(self, key, *values): return self.r.rpushx(key, *values)
	
	def delete(self, key): return self.r.delete(key)
	
	# WARNING!
	def flushdb(self): return self.r.flushdb()
	
	# read
	def get(self, key): 
		rt = self.r.get(key)
		return self.__postprocess(rt)
	
	def lrange(self, key, start, stop):
		rt = self.r.lrange(key, start, stop)
		return self.__postprocess(rt)
		
	def exists(self, key):
		return self.r.exists(key)
		
	def sismember(self, key, member):
		return self.r.sismember(key, member)
		
	def llen(self, key):
		return self.__postprocess(self.r.llen(key))
		
	def lindex(self, key, index):
		return self.__postprocess(self.r.lindex(key, index))
	
