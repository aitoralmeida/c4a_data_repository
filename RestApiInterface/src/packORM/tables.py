# -*- coding: utf-8 -*-

"""
This file uses SQL alchemy declarative base model to create SQL Tables.

Here we define tables, relationships between tables and so on.

"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy import Column, Integer, String, Sequence, Float, Table, ForeignKey, TIMESTAMP, Text, TypeDecorator
from PasswordHash import PasswordHash
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)


__author__ = 'Rubén Mulero'
__copyright__ = "foo"   # we need?¿

# Global variable declatarive base
Base = declarative_base()


class Password(TypeDecorator):
    """Allows storing and retrieving password hashes using PasswordHash."""
    impl = Text

    def __init__(self, rounds=12, **kwds):
        self.rounds = rounds
        super(Password, self).__init__(**kwds)

    def process_bind_param(self, value, dialect):
        """Ensure the value is a PasswordHash and then return its hash."""
        return self._convert(value).hash

    def process_result_value(self, value, dialect):
        """Convert the hash to a PasswordHash, if it's non-NULL."""
        if value is not None:
            return PasswordHash(value, rounds=self.rounds)

    def validator(self, password):
        """Provides a validator/converter for @validates usage."""
        return self._convert(password)

    def _convert(self, value):
        """Returns a PasswordHash from the given string.

        PasswordHash instances or None values will return unchanged.
        Strings will be hashed and the resulting PasswordHash returned.
        Any other input will result in a TypeError.
        """
        if isinstance(value, PasswordHash):
            return value
        elif isinstance(value, basestring):
            return PasswordHash.new(value, self.rounds)
        elif value is not None:
            raise TypeError(
                'Cannot convert {} to a PasswordHash'.format(type(value)))


def create_tables(p_engine):
    """
    Create all tables

    :param p_engine: Conex engine
    :return: None
    """
    return Base.metadata.create_all(p_engine)


# Association tables for m2m Relationships
class UserActionRel(Base):
    """

    User ---> Action m2m REL

    """
    __tablename__ = 'user_action_rel'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    action_id = Column(Integer, ForeignKey('action.id'), primary_key=True)
    date = Column(TIMESTAMP)
    action = relationship("Action")


class UserLocationRel(Base):
    """

    User ---> Location m2m REL

    """
    __tablename__ = 'user_location_rel'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    location_id = Column(Integer, ForeignKey('location.id'), primary_key=True)
    date = Column(TIMESTAMP)
    location = relationship("Location")


# Tables
class User(Base):
    """
    Base data of the users
    """
    __tablename__ = 'user'

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    username = Column(Text, nullable=False, unique=True)
    password = Column(Password(rounds=13), nullable=False)
    # Or specify a cost factor other than the default 12
    # password = Column(Password(rounds=10))
    # Without rounds System will use 12 rounds by default
    name = Column(String(50))
    lastname = Column(String(50))
    genre = Column(String(12))
    age = Column(Integer)
    #todo uncoment for user roles
    #role = Column(String(15), default='user')
    # one2many
    payload = relationship("Payload")
    # m2m
    action = relationship("UserActionRel")
    location = relationship("UserLocationRel")

    def __repr__(self):
        return "<User(name='%s', lastname='%s', genre='%s', age='%s')>" % (
            self.name, self.lastname, self.genre, self.age)

    def to_json(self):
        return dict(name=self.name, lastname=self.lastname,
                #registered_on=self.registered_on.isoformat()
                genre=self.genre, age=self.age )

    # Password Encryption validation
    @validates('password')
    def _validate_password(self, key, password):
        return getattr(type(self), key).type.validator(password)



    # # Token management
    # def generate_auth_token(self, app, expiration=600):
    #     """
    #     This method generates a new auth token to the user.
    #
    #     :param app: Flask application Object
    #     :param expiration: Expiration time of the token
    #
    #     :return: A string with the token.
    #     """
    #     s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
    #     return s.dumps({'id': self.id})
    #
    # @staticmethod
    # def verify_auth_token(token, app):
    #     """
    #     This method verify user's token
    #
    #     :param token: Token information
    #     :param app: Flask application Object
    #
    #     :return: User ID
    #     """
    #     s = Serializer(app.config['SECRET_KEY'])
    #     try:
    #         data = s.loads(token)
    #     except SignatureExpired:
    #         return None  # valid token, but expired
    #     except BadSignature:
    #         return None  # invalid token
    #     return data



class Action(Base):
    """
    Action registration
    """
    __tablename__ = 'action'

    id = Column(Integer, Sequence('action_id_seq'), primary_key=True)
    action_name = Column(String(75))
    rating = Column(Float(3))
    # one2many
    extra = relationship("Extra")
    payload = relationship("Payload")

    def __repr__(self):
        return "<Action(action_name='%s', rating='%s')>" % (
            self.action_name, self.rating)


class Location(Base):
    """
    Users location in a specific time
    """
    __tablename__ = 'location'

    id = Column(Integer, Sequence('location_id_seq'), primary_key=True)
    location = Column(String(75))

    def __repr__(self):
        return "<Location(location='%s')>" % self.location


class Extra(Base):
    """
    Extra infor from Pilot
    """
    __tablename__ = 'extra'

    id = Column(Integer, Sequence('extra_id_seq'), primary_key=True)
    pilot = Column(String(75))
    city = Column(String(50))
    action_id = Column(Integer, ForeignKey('action.id'))

    def __repr__(self):
        return "<Extra(pilot='%s', city='%s')>" % (self.pilot, self.city)


#todo delete it we don't need it
class Payload(Base):
    """
    Payload: User and GPS position of the current action
    """
    __tablename__ = 'payload'

    id = Column(Integer, Sequence('payload_id_seq'), primary_key=True)
    position = Column(String(75))
    user_id = Column(Integer, ForeignKey('user.id'))
    action_id = Column(Integer, ForeignKey('action.id'))

    def __repr__(self):
        return "<Payload(position='%s')>" % self.position
