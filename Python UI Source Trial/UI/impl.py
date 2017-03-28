import security
from base64 import b64encode, b64decode

msg1 = "Hello Tony, I am Jarvis!"
msg2 = "Hello Toni, I am Jarvis!"
keysize = 2048
(public, private) = security.newkeys(keysize)
encrypted = b64encode(security.encrypt(msg1, private))
decrypted = security.decrypt(b64decode(encrypted), private)
signature = b64encode(security.sign(msg1, private, "SHA-512"))
verify = security.verify(msg1, b64decode(signature), public)

# print(private.exportKey('PEM'))
# print(public.exportKey('PEM'))
print("Encrypted: " + encrypted)
print("Decrypted: '%s'" % decrypted)
print("Signature: " + signature)
print("Verify: %s" % verify)
security.verify(msg2, b64decode(signature), public)