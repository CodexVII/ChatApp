from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto import Random
from PyQt4 import QtCore
import sys
import base64
import random

##################################################
# setting up payload
##################################################
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


##################################################
# test  segmented encrypt/decrypt
# Encode message in base64
# encrypt in 128 segments
# decrypt in 128 segments
# decode message in base64
##################################################
def heavyEncrypt(plaintext, public_key):
    result = []
    step = 0
    text = base64.b64encode(plaintext)
    while 1:
        # read 128 characters at a time
        s = text[step * 128:(step + 1) * 128]
        if not s:
            break
        result.append(public_key.encrypt(s, None)[0])
        step += 1
    return ''.join(result)


def heavyDecrypt(ciphertext, private_key):
    step = 0
    result = []
    while 1:
        s = ciphertext[step * 128:(step + 1) * 128]
        if not s:
            break
        result.append(private_key.decrypt(s))
        step += 1
    # assumes data was encoded in base64
    return base64.b64decode(''.join(result))

encrypted = heavyEncrypt("hellob", pub_B)
print heavyDecrypt(encrypted, key_B)

##################################################
# test QByteArray reconstruction
##################################################
# convert QByteArray to String
# encrypt
new_block = QtCore.QByteArray(str(block))
read = QtCore.QDataStream(new_block, QtCore.QIODevice.ReadOnly)
read.readUInt16()
print "Rebuilt challenge: " + read.readString()
read.readUInt16()
print "Rebuilt signature: " + read.readString()

##################################################
# test encrypting/decrypting block
##################################################
encrypted_block = heavyEncrypt(block, pub_B)
decrypted_block = heavyDecrypt(encrypted_block, key_B)
# print "Orig Block: " + block
# print "Decrypted Block: " + decrypted_block
# encrypted_block = pub_B.encrypt(str(block), None)[0]
# decrypted_block = key_B.decrypt(encrypted_block)
rebuild = QtCore.QByteArray(decrypted_block)
re = QtCore.QDataStream(rebuild, QtCore.QIODevice.ReadOnly)
#
re.readUInt16()
loot = re.readString()
re.readUInt16()
lootSign = re.readString()
print rebuild
print "Challenge from decrypted block: " + loot
print "Signature from decrypted block: " + lootSign

##################################################
# encrypting decrypting
##################################################
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
print pub_A.verify(sha2.hexdigest(), (long(lootSign),))
