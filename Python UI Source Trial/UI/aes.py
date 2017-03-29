import base64
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHA256


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


if __name__ == "__main__":
    # create key
    ian = AESCipher(key="1535022712713798117")

    # create data (str)
    data = "Hello"
    # encrypt data
    encrypted = ian.encrypt(data)

    # decrypt data
    decrypted = ian.decrypt(encrypted)

    # print data
    print (encrypted)
    print (decrypted)
