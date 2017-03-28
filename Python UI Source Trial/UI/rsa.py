from Crypto.PublicKey import RSA
from Crypto import Random
import hashlib
import base64
import ast  # ast = Abstract Syntax Trees - used for decrypting message

random_generator = Random.new().read
random_generator2 = Random.new().read
key_A = RSA.generate(1024, random_generator)  # generate public & private key
key_B = RSA.generate(1024, random_generator2)  # generate public & private key

# 1024 = key length (bits) of RSA modulus

publickey_A = key_A.publickey()  # pub key export for exchange
publicKey_B = key_B.publickey()

privkey = key_A.has_private()

data = str("1231")
hash = hashlib.sha256(data).hexdigest()

# encrypted = publicKey_B.encrypt(key_A.sign(hash, 32)[0], 32)  # 32 = number of bit
# message to encrypt is in the above line 'encrypt this message'

# second return is the random number don't use
signature = key_A.sign(hash, '')[0]

# print "Signature " + str(signature[0])
to_join = []
step = 0

# print str(signature[0])[0:128]
while 1:
    # read 128 characters at a time
    s = str(signature)[step * 128:(step + 1) * 128]
    s.rjust(128, '0')
    print "Portion: " + str(step) + " " + s
    if not s:
        break
    to_join.append(publicKey_B.encrypt(s, None)[0])
    step += 1
encrypted = ''.join(to_join)
# print "Encrypted " + str(encrypted)

step = 0
result = []
while step < len(to_join):
    s = encrypted[step * 128:(step + 1) * 128]

    if not s:
        break
    to_join.append(key_B.decrypt(s))
    # print "Portion: " + str(step) + " " + to_join[step]
    print step
    step += 1
decrypted = ''.join(to_join)
sig = str(decrypted)[len(decrypted) - len(str(signature)):]
print str(decrypted)[len(decrypted) - len(str(signature)):]
print key_B.verify(hash, (long(signature),''))


# encrypted = publicKey_B.encrypt(str(signature[0])[0:128], None)

# print "Encrypted signature " + str(len(str(encrypted[0])))
# encrypted2 = base64.b64encode(str(encrypted[0]))
# print 'Output of Encrypted Message:', encrypted  # ciphertext
# f = open('encryption.txt', 'w')
# f.write(str(encrypted))  # write ciphertext to file
# f.close()
#
# # decrypted code below
#
# f = open('encryption.txt', 'r')
# message = f.read()
#
# first = key_B.decrypt(ast.literal_eval(str(encrypted)))

###################################################################################################################################

# newHash = hashlib.sha256(data).hexdigest()
# print "Encoded signature (encrypted) " + str(encrypted2[0])
# print "Key size " + str(key_B.size())
# print "Decoded signature (encrypted) " + str(base64.b64decode(str(encrypted2))[0:128])
# sign_decrypted = key_B.decrypt(base64.b64decode(encrypted2))
# sign_decrypted = key_B.decrypt()
# print sign_decrypted
# signature = key_A.sign(hash, '')
# decrypted = publickey_A.verify(newHash, signature)  # literal_eval = used to safely evaluated the encrypted text
# key.decrypt will not evaluate str(encrypt) without
# literal_eval.  Error = str too large

# print 'Decrypted Message:', decrypted

# f = open('encryption.txt', 'w')
# f.write(str(message))
# f.write(str(decrypted))
# f.close()
