from Crypto.PublicKey import RSA
from Crypto import Random
import ast  # ast = Abstract Syntax Trees - used for decrypting message

random_generator = Random.new().read
key = RSA.generate(1024, random_generator) # generate public & private key
                                            # 1024 = key length (bits) of RSA modulus

publickey = key.publickey() # pub key export for exchange
privkey = key.has_private()

encrypted = publickey.encrypt('This is my hidden message.. Hi guys!', 32)  # 32 = number of bit
# message to encrypt is in the above line 'encrypt this message'

print 'Output of Encrypted Message:', encrypted # ciphertext
f = open ('encryption.txt', 'w')
f.write(str(encrypted)) # write ciphertext to file
f.close()

# decrypted code below

f = open('encryption.txt', 'r')
message = f.read()

decrypted = key.decrypt(ast.literal_eval(str(encrypted))) # literal_eval = used to safely evaluated the encrypted text
                                                          # key.decrypt will not evaluate str(encrypt) without
                                                          # literal_eval.  Error = str too large

print 'Decrypted Message:', decrypted

f = open ('encryption.txt', 'w')
f.write(str(message))
f.write(str(decrypted))
f.close()