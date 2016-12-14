# -*- coding: utf-8 -*-


"""
This is an Encrtyption handler class based on Elmer de Looff implementation of PasswordHash.

The goal of this class is to encrypt/decrypt database column values to add an extra layer of security
to sensible data.

Use new method to encrypt your desired data.

Use __eq__ to compare your data with encrypted stored datada from database.

Use decrypt to obtain the real value from encrypted value on database

"""


import binascii
from sqlalchemy.ext.mutable import Mutable
from Crypto.Cipher import AES


__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján", "Elmer de Looff"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


class Encryption(Mutable):
    def __init__(self, value_, cipher_key=None):
        self.value = str(value_)
        self.cipher_key = cipher_key

    def __eq__(self, candidate):
        """
        Compares the candidate with encrypted stored value.
        """
        if isinstance(candidate, basestring):
            if isinstance(candidate, unicode):
                candidate = candidate.encode('utf8')
            cipher = AES.new(self.cipher_key)
            if candidate == cipher.decrypt(binascii.unhexlify(self.value)).rstrip():
                return True
        return False

    def __repr__(self):
        """Simple object representation."""
        return '<{}>'.format(type(self).__name__)

    def decrypt(self):
        """
        Decrypt the value and returns its original meaning.

        decrypt = Object.value

        :return: The value decrypted.
        """
        cipher = AES.new(self.cipher_key)
        return cipher.decrypt(binascii.unhexlify(self.value)).rstrip()

    @classmethod
    def coerce(cls, cipher_key, value):
        """Ensure that loaded values are Encryption values."""
        if isinstance(value, Encryption):
            return value
        return super(Encryption, cls).coerce(cipher_key, value)

    @classmethod
    def new(cls, value, cipher_key):
        """Returns a new Encryption object for the given value and cipher key."""
        assert len(cipher_key) == 32, 'AES cipher_key should be 32'
        if isinstance(value, unicode):
            value = value.encode('utf8')
        return cls(cls._new(value, cipher_key))

    @staticmethod
    def _new(value, cipher_key):
        """Returns a new AES encrypted value for the given value and cipher key."""
        cipher = AES.new(cipher_key)
        value += " " * (16 - (len(value) % 16))
        return binascii.hexlify(cipher.encrypt(value))

