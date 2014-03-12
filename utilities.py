

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
"""
from json import JSONEncoder

def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)

_default.default = JSONEncoder().default # save unmodified default
JSONEncoder.default = _default # replacement



#==============================================================================
# RLP OPERATIONS
#==============================================================================
	
def RLP_WRAP_DESERIALIZE(rlpIn):
	if rlpIn[0] >= 0xc0:
		if rlpIn[0] > 0xf7:
			sublenlen = rlpIn[0].int() - 0xf7
			sublen = rlpIn[1:sublenlen+1].int()
			msg = rlpIn[sublenlen+1:sublenlen+sublen+1]
			rem = rlpIn[sublenlen+sublen+1:]
		
		else:
			sublen = rlpIn[0].int() - 0xc0
			msg = rlpIn[1:sublen+1]
			rem = rlpIn[sublen+1:]
			
		o = []
		while len(msg) > 0:
			t, msg = RLP_WRAP_DESERIALIZE(msg)
			o.append(t)
		return o, rem
	
	elif rlpIn[0] > 0xb7:
		subsublen = rlpIn[0].int() - 0xb7
		sublen = rlpIn[1:subsublen+1].int()
		msg = rlpIn[subsublen+1:subsublen+sublen+1]
		rem = rlpIn[subsublen+sublen+1:]
		return msg, rem
		
	elif rlpIn[0] >= 0x80:
		sublen = rlpIn[0].int() - 0x80
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
			
	
