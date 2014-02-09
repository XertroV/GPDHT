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
	h = i.__format__('x')
	return ('0'*(len(h)%2)+h).decode('hex')
	
def sumSI(s,i): return i2s(s2i(s)+i)
def sumIS(i,s): return i2s(s2i(s)+i)
	
def sumSS(s1,s2): return i2s(s2i(s1)+s2i(s2))

def sGT(s1, s2): return s2i(s1) > s2i(s2)
	
	
#==============================================================================
# CRYPTO
#==============================================================================




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
