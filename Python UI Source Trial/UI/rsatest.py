from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto import Random
from PyQt4 import QtCore
import sys
import base64
import random

# generate keys
key_A = RSA.generate(1024, Random.new().read)
key_B = RSA.generate(1024, Random.new().read)

pub_A = key_A.publickey()
pub_B = key_B.publickey()

# generate challenge
challenge = str(random.randint(0, 65000))
print "Challenge: " + challenge

# sign
sha = SHA256.new()
sha.update(challenge)
signature = key_A.sign(sha.hexdigest(), None)[0]
print "Signature: " + str(signature)

# encrypt the signature and challenge
cipher = challenge + str(signature)
print "Cipher: " + cipher
# write to qByteArray
block = QtCore.QByteArray()
out = QtCore.QDataStream(block, QtCore.QIODevice.ReadWrite)
# write the challenge
out.writeUInt16(0)
out.writeString(challenge)
out.writeUInt16(0)
out.writeString(str(signature))
# read the challenge
out.device().seek(0)
out.readUInt16()
data = out.readString()
out.readUInt16()
embedded_sig = out.readString()

# test encrypting block
# print len(block)

# encrypted_block = pub_B.encrypt(str(block), None)[0]
# decrypted_block = key_B.decrypt(encrypted_block)
# rebuild = QtCore.QByteArray(decrypted_block)
# re = QtCore.QDataStream(rebuild, QtCore.QIODevice.ReadOnly)
#
# print "Size: " + str(re.readUInt16())
# loot = re.readFloat()
# print rebuild
# print loot


# test QByteArray reconstruction
# convert QByteArray to String
# encrypt
new_block = QtCore.QByteArray(str(block))
read = QtCore.QDataStream(new_block, QtCore.QIODevice.ReadOnly)
read.readUInt16()
print "Rebuilt challenge: " + str(read.readFloat())
read.readUInt16()
print "Rebuilt signature: " + str(read.readFloat())


print "Challenge: " + str(data)
print "Signature: " + str(embedded_sig)
print "Signature length: " + str(len(str(signature)))
encrypted = pub_B.encrypt(signature, None)[0]
print "Encrypted signature: " + str(encrypted)

# decrypt in chunks
decrypted = key_B.decrypt(encrypted)
print "Decrypted signature: " + str(decrypted)

# verify
sha2 = SHA256.new()
sha2.update(challenge)
print sha2.hexdigest()
print pub_A.verify(sha2.hexdigest(), (decrypted,))
