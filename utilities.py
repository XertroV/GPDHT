

#==============================================================================
# CONST
#==============================================================================

ZERO = chr(0)

#==============================================================================
# LOGIC
#==============================================================================

def xor_strings(xs, ys):
    return "".join(chr(ord(x) ^ ord(y)) for x, y in zip(xs, ys))
	
	
#==============================================================================
# DATA TYPES
#==============================================================================


def s2i(s):
    return long(s.encode('hex'), 16)
    
def i2s(i):
	return i2h(i).decode('hex')
	
def i2h(i):
	h = i.__format__('x')
	return '0'*(len(h)%2)+h
	
	
def sumSI(s,i): return i2s(s2i(s)+i)
def sumIS(i,s): return i2s(s2i(s)+i)
	
def sumSS(s1,s2): return i2s(s2i(s1)+s2i(s2))

def sGT(s1, s2): return s2i(s1) > s2i(s2)
	
	
#==============================================================================
# CRYPTO
#==============================================================================

from hashlib import sha256

def sha256Hash(plaintext):
	return sha256(plaintext).digest()
	


#==============================================================================
# NETWORK
#==============================================================================

def packTarget(upt):
	pad = 0
	zero = chr(0)
	while upt[0] == chr(0):
		pad += 1
		upt = upt[1:]
	return upt[:3]+chr(pad)
	
def unpackTarget(pt):
	pt = str(pt)
	pad = ord(pt[3])
	zero = chr(0)
	sigfigs = pt[:3]
	rt = zero*pad + sigfigs + zero*(32-3-pad)
	return long(rt.encode('hex'),16)


#==============================================================================
# JSON HELPER
#==============================================================================

"""Module that monkey-patches json module when it's imported so
JSONEncoder.default() automatically checks for a special "to_json()"
method and uses it to encode the object if found.
-- Found on stack exchange
User: martineau
URL: http://stackoverflow.com/questions/18478287/making-object-json-serializable-with-regular-encoder
"""
from json import JSONEncoder

def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)

_default.default = JSONEncoder().default # save unmodified default
JSONEncoder.default = _default # replacement


def json_str_to_bant(obj):
	if isinstance(obj, str):
		return BANT(obj)
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

