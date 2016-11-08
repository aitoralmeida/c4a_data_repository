# -*- coding: utf-8 -*-

"""
This is an implementation of Bcrypt to encrypt all passwords in database.

It is very recommended to create new passwords with 12 or more rounds.

Use new method to set new password.
Use __eq__ to compare if the password given is correct.

"""

import bcrypt
from sqlalchemy.ext.mutable import Mutable


__author__ = 'Elmer de Looff'


class PasswordHash(Mutable):
    def __init__(self, hash_, rounds=None):
        assert len(hash_) == 60, 'bcrypt hash should be 60 chars.'
        assert hash_.count('$'), 'bcrypt hash should have 3x "$".'
        self.hash = str(hash_)
        self.rounds = int(self.hash.split('$')[2])
        self.desired_rounds = rounds or self.rounds

    def __eq__(self, candidate):
        """Hashes the candidate string and compares it to the stored hash.

        If the current and desired number of rounds differ, the password is
        re-hashed with the desired number of rounds and updated with the results.
        This will also mark the object as having changed (and thus need updating).
        """
        if isinstance(candidate, basestring):
            if isinstance(candidate, unicode):
                candidate = candidate.encode('utf8')
            if self.hash == bcrypt.hashpw(candidate, self.hash):
                if self.rounds < self.desired_rounds:
                    self._rehash(candidate)
                return True
        return False

    def __repr__(self):
        """Simple object representation."""
        return '<{}>'.format(type(self).__name__)

    @classmethod
    def coerce(cls, key, value):
        """Ensure that loaded values are PasswordHashes."""
        if isinstance(value, PasswordHash):
            return value
        return super(PasswordHash, cls).coerce(key, value)

    @classmethod
    def new(cls, password, rounds):
        """Returns a new PasswordHash object for the given password and rounds."""
        if isinstance(password, unicode):
            password = password.encode('utf8')
        return cls(cls._new(password, rounds))

    @staticmethod
    def _new(password, rounds):
        """Returns a new bcrypt hash for the given password and rounds."""
        return bcrypt.hashpw(password, bcrypt.gensalt(rounds))

    def _rehash(self, password):
        """Recreates the internal hash and marks the object as changed."""
        self.hash = self._new(password, self.desired_rounds)
        self.rounds = self.desired_rounds
        self.changed()
