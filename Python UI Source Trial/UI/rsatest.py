from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto import Random
from PyQt4 import QtCore
import base64
import random


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


def sha256(data):
    digest = SHA256.new()
    digest.update(data)
    return digest.digest()

def heavyDecrypt(ciphertext, private_key):
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


def test1():
    ##################################################
    # setting up payload
    ##################################################
    # generate keys
    key_A = RSA.generate(1024)
    key_B = RSA.generate(1024)

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




    encrypted = heavyEncrypt("hellob", pub_B)
    print heavyDecrypt(encrypted, key_B)

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
    encrypted_block = heavyEncrypt(block, pub_B)
    print "-------------------------"
    print "Encrypted"
    print encrypted_block
    print "-------------------------"

    # decrypt
    decrypted_block = heavyDecrypt(encrypted_block, key_B)

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


def writeRaw(stream, data):
    old_pos = stream.device().pos()
    stream.writeUInt16(0)
    stream.writeRawData(data)
    new_pos = stream.device().pos()
    size = new_pos - old_pos - 2  # -2 for UInt16
    stream.device().seek(old_pos)
    stream.writeUInt16(size)
    stream.device().seek(new_pos)


def blockBuilder(*args):
    block = QtCore.QByteArray()
    stream = QtCore.QDataStream(block, QtCore.QIODevice.WriteOnly)

    print args
    for arg in args:
        if str(type(arg)) in "<type 'str'>":
            stream.writeString(arg)
        elif str(type(arg)) in "<class 'PyQt4.QtCore.QByteArray'>":
            stream.writeBytes(arg)
        else:
            print "Argument not valid"

    return block


def blockReader(block, items):
    stream = QtCore.QDataStream(block, QtCore.QIODevice.ReadOnly)
    result = []
    for item in items:
        if str(item) in "<type 'str'>":
            result.append(stream.readString())
        elif str(item) in "<class 'PyQt4.QtCore.QByteArray'>":
            result.append(stream.readBytes())
        else:
            print "Item not valid"
    return tuple(result)


def test2():
    key_A = RSA.generate(1024)
    key_B = RSA.generate(1024)

    pub_A = key_A.publickey()
    pub_B = key_B.publickey()

    # create block
    # write encrypted
    # retrieve block
    # read encrypted

    # plain = QtCore.QByteArray()
    #
    # encrypted = heavyEncrypt("note", key_B)
    # decrypted = heavyDecrypt(encrypted, key_B)
    for i in range(1):
        print "-------------------------------------"
        print "iter %d" % i
        print "-------------------------------------"
        plain = QtCore.QByteArray()
        plainWriter = QtCore.QDataStream(plain, QtCore.QIODevice.WriteOnly)
        block = blockBuilder("This is real", "This is me")
        encrypted = heavyEncrypt(block, key_B)
        plainWriter.writeString("A")
        plainWriter.writeString("B")
        writeRaw(plainWriter, encrypted)

        # print encrypted


        enc = QtCore.QByteArray(plain)
        reader = QtCore.QDataStream(enc, QtCore.QIODevice.ReadOnly)
        reader.readString()
        reader.readString()
        size = reader.readUInt16()
        decrypted = heavyDecrypt(reader.readRawData(size), key_B)
        block = QtCore.QByteArray(decrypted)
        msg1, msg2 = blockReader(block, (str, str))
        print msg1
        print msg2
        # decrypted = heavyDecrypt(encrypted, key_B)
        # print decrypted


if __name__ == '__main__':
    test2()
