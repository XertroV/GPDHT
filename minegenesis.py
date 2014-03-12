from hashlib import sha256

from utilities import *

ghl = [
	'00000001'.decode('hex'),
	'0000000000000000000000000000000000000000000000000000000000000000'.decode('hex'),
	'0000000000000000000000000000000000000000000000000000000000000000'.decode('hex'),
	'0fffff02'.decode('hex'),
	'00000000'.decode('hex')
	]

def cgb(ghl):
	return ''.join(ghl)

gh = cgb(ghl)

def hash(m):
    return sha256(m).digest()

def s2i(s):
    return long(s.encode('hex'), 16)

target = unpackTarget(ghl[3])
print "Target : %064x" % target
c = 0
while True:
    h = hash(cgb(ghl))
    c += 1
    if s2i(h) < target:
            print 'Success'
            print h.encode('hex')
            print 'nonce:', ghl[2].encode('hex')
            break
    ghl[2] = hash(ghl[2])[:8]
    if c % 1000 == 0:
            print c, 'COUNT'
			
	
