from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random
from PyQt4 import QtCore
import base64
import random


##############################################
# RSA (Authentication)
##############################################

def heavyRSAEncrypt(plaintext, public_key):
    result = []
    step = 0
    text = base64.b64encode(plaintext)
    print "Encrypt length: " + str(len(plaintext))
    print "Encoded: " + text
    while 1:
        # read 128 characters at a time
        s = text[step * 128:(step + 1) * 128]
        if not s:
            break
        result.append(public_key.encrypt(s, None)[0])
        step += 1
    return ''.join(result)


def heavyRSADecrypt(ciphertext, private_key):
    step = 0
    result = []
    text = str(ciphertext)
    # print ciphertext
    while 1:
        s = text[step * 128:(step + 1) * 128]
        if not s:
            break
        result.append(private_key.decrypt(s))
        step += 1
    # assumes data was encoded in base64
    print "Decoded: " + ''.join(result)
    outcome = base64.b64decode(''.join(result))

    print "Decrypt length: " + str(len(outcome))
    return outcome


def sign(message, private_key):
    signer = RSA.importKey(private_key)
    digest = SHA256.new()
    digest.update(message)
    return signer.sign(digest.hexdigest(), None)[0]


def verify(message, signature, public_key):
    verifier = RSA.importKey(public_key)
    digest = SHA256.new()
    digest.update(message)
    return verifier.verify(digest.hexdigest(), (long(signature),))


##############################################
# SHA256 (Integrity)
##############################################

def sha256(data):
    digest = SHA256.new()
    digest.update(data)
    return digest.digest()


##############################################
# AES (Confidentiality)
##############################################

class AESCipher(object):
    def __init__(self, key):
        self.bs = 16

        # represent key in 32 byte form
        sha = SHA256.new()
        sha.update(key)
        self.key = sha.digest()

    def encrypt(self, raw):
        raw_padded = self._pad(str(raw))
        iv = Random.new().read(AES.block_size)

        cipher = AES.new(self.key, AES.MODE_CFB, iv)
        encoded = base64.b64encode(iv + cipher.encrypt(raw_padded))
        print "Raw (Encrypt): " + raw
        print "Raw_padded (Encrypt)" + raw_padded
        print "Encoded (Encrypt): " + encoded
        return encoded

    def decrypt(self, enc):
        decoded = base64.b64decode(str(enc))
        # 0 to block size
        iv = decoded[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CFB, iv)
        result = self._unpad(cipher.decrypt(decoded[AES.block_size:]))
        print "Encoded (Decrypt): " + enc
        print "Decoded (Decrypt): " + decoded
        print "Result (Decrypt): " + result
        return result

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]




if __name__ == '__main__':
    ##################################################
    # setting up payload
    ##################################################
    # generate keys
    print Random.new().read
    print Random.new().read
    key_A = RSA.generate(1024)
    key_B = RSA.generate(1024)

    print key_A.exportKey()
    print key_B.exportKey()
    keb_B = RSA.importKey(key_A.publickey().exportKey()).exportKey()

    print keb_B
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

    # write to qByteArray
    block = QtCore.QByteArray()
    out = QtCore.QDataStream(block, QtCore.QIODevice.ReadWrite)
    # write the challenge
    out.writeString(challenge)
    out.writeString(str(signature))

    ##################################################
    # Test appending block into already existing block
    ##################################################
    # write block into it
    block2 = QtCore.QByteArray()
    out2 = QtCore.QDataStream(block2, QtCore.QIODevice.ReadWrite)
    out2.writeString("Hey! This was appended.")
    out2.writeString("New message")
    old = out2.device().pos()
    out2.writeUInt16(0)
    out2.writeRawData("I am a file")
    new = out2.device().pos()
    size = new - old - 2
    out2.device().seek(old)
    out2.writeUInt16(size)
    out2.device().seek(new)
    old = out2.device().pos()
    out2.writeUInt16(0)
    out2.writeRawData("I am a file2")
    new = out2.device().pos()
    size = new - old
    out2.device().seek(old)
    out2.writeUInt16(size)
    out2.device().seek(new)
    # out2.writeString("Don't print me")    # can't add strings after raw data
    out.writeRawData(block2)
    print "block: " + block2

    # read the challenge
    out.device().seek(0)
    data = out.readString()  # challenge
    embedded_sig = out.readString()  # signature
    # extra reads from appended block
    print out.readString()  # msg1
    print out.readString()  # msg2
    toread = out.readUInt16()
    print out.readRawData(toread)  # rawData
    toread = out.readUInt16()
    print out.readRawData(toread)  # rawData

    # print out.readString()




    encrypted = heavyRSAEncrypt("hellob", pub_B)
    print heavyRSADecrypt(encrypted, key_B)

    ##################################################
    # test QByteArray reconstruction
    ##################################################
    new_block = QtCore.QByteArray(str(block))
    read = QtCore.QDataStream(new_block, QtCore.QIODevice.ReadOnly)

    print "Rebuilt challenge: " + read.readString()
    print "Rebuilt signature: " + read.readString()

    ##################################################
    # test encrypting/decrypting block
    ##################################################
    # encrypt the signature and challenge
    encrypted_block = heavyRSAEncrypt(block, pub_B)
    # decrypt
    decrypted_block = heavyRSADecrypt(encrypted_block, key_B)
    rebuild = QtCore.QByteArray(decrypted_block)
    # read
    re = QtCore.QDataStream(rebuild, QtCore.QIODevice.ReadOnly)
    loot = re.readString()
    lootSign = re.readString()

    print "Challenge from decrypted block: " + loot
    print "Signature from decrypted block: " + lootSign

    ##################################################
    # verify message
    ##################################################
    sha2 = SHA256.new()
    sha2.update(loot)
    print sha2.hexdigest()
    print pub_A.verify(sha2.hexdigest(), (long(lootSign),))
