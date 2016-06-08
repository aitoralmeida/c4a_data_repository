# -*- coding: utf-8 -*-

"""
This file uses SQL alchemy declarative base model to create SQL Tables.

Here we define tables, relationships between tables and so on.

"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy import Column, Integer, String, Boolean, Sequence, Float, BigInteger , Table, ForeignKey, TIMESTAMP, Text, TypeDecorator
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
class ExecutedAction(Base):
    """
    Multi relationship table.

    User - Action -- Activity -- Location
    """
    __tablename__ = 'executed_action'

    id = Column(Integer, Sequence('executed_action_id_seq'), primary_key=True)
    #user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'))
    user_id = Column(String(75), ForeignKey('user.id'))
    action_id = Column(Integer, ForeignKey('action.id'))
    activity_id = Column(Integer, ForeignKey('activity.id'), nullable=True)
    location_id = Column(Integer, ForeignKey('location.id'))
    date = Column(TIMESTAMP)
    # Asociated information
    rating = Column(Integer)
    sensor_id = Column(Integer)
    payload = Column(String(50))
    extra_information = Column(Text)
    # Relationship with other TABLES
    action = relationship("Action")
    activity = relationship("Activity")
    location = relationship("Location")
    # m2m
    risk = relationship('RiskExecutedActionRel')


class RiskBehaviorRel(Base):
    """
    Behavior <---> Risk M2m REL
    """
    __tablename__ = 'risk_behavior_rel'

    behavior_id = Column(Integer, ForeignKey('behavior.id'), primary_key=True)
    risk_id = Column(Integer, ForeignKey('risk.id'), primary_key=True)
    risk = relationship('Risk')


class RiskExecutedActionRel(Base):
    """
    ExecutedAction < --> Risk
    """
    __tablename__ = 'risk_executed_action_rel'

    executed_action_id = Column(Integer, ForeignKey('executed_action.id'), primary_key=True)
    risk_id = Column(Integer, ForeignKey('risk.id'), primary_key=True)
    risk = relationship('Risk')


# Tables



class UserInRole(Base):
    """
    Base data of the users
    """
    __tablename__ = 'user_in_role'

    id = Column(Integer, Sequence('user_in_role_seq'), primary_key=True)
    username = Column(Text, nullable=False, unique=True)
    password = Column(Password(rounds=13), nullable=False)
    # Or specify a cost factor other than the default 13
    # password = Column(Password(rounds=10))
    # Without rounds System will use 13 rounds by default
    role = Column(String(15), default='user')
    # m2m
    #action = relationship("ExecutedAction")
    # Fkey
    pilot_id = Column(Integer, ForeignKey('pilot.id'))

    def __repr__(self):
        return "<UserInRole(username='%s', password='%s', role='%s')>" % (
            self.username, self.password, self.role)

    def to_json(self):
        return dict(username=self.username,
                    password=self.password,
                    role=self.role)

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
    action_name = Column(String(50))
    category = Column(String(25))

    def __repr__(self):
        return "<Action(action_name='%s', category='%s')>" % (
            self.action_name, self.category)


class Location(Base):
    """
    Users location in a specific time
    """
    __tablename__ = 'location'

    id = Column(Integer, Sequence('location_id_seq'), primary_key=True)
    location_name = Column(String(75))
    indoor = Column(Boolean)
    # One2Many
    pilot = relationship('Pilot')

    def __repr__(self):
        return "<Location(location_name='%s', indoor='%s')>" % (self.location_name, self.indoor)


class Activity(Base):
    """
    Activity is a collection of different actions. For example "Make breakfast is an activity and could have some actions
    like:

        --> Put the milk in the bowl
        --> Open the fridge
        --> .....
    """
    __tablename__ = 'activity'

    id = Column(Integer, Sequence('activity_id_seq'), primary_key=True)
    activity_name = Column(String(50))

    # Fkeys
    behavior_id = Column(Integer, ForeignKey('behavior.id'))

    def __repr__(self):
        return "<Activity(activity_name='%s')>" % self.activity_name


class Behavior(Base):
    """
    Behavior is a collection os different activities. For example some everyday activities can result on "Go to the park
    at weekdays"
    """

    __tablename__ = 'behavior'

    id = Column(Integer, Sequence('behavior_id_seq'), primary_key=True)
    behavior_name = Column(String(50))
    # one2many relantionship
    activity = relationship('Activity')
    # m2m relationship
    risk = relationship('RiskBehaviorRel')

    def __repr__(self):
        return "<Behavior(behavior_name='%s', risk='%s')>" % (self.behavior_name, self.risk)


class Risk(Base):
    """
    Some actions or behavior have an associated % of risk. For example, it is possible that "Go to the park at weekdays"
    has a % of chance to have MCI if the user performs some strange actions.
    """

    __tablename__ = 'risk'

    id = Column(Integer, Sequence('risk_id_seq'), primary_key=True)
    risk_name = Column(String(50))
    ratio = Column(Float(3))
    description = Column(String(255))

    def __repr__(self):
        return "<Risk(risk_name='%s', ratio='%s', description='%s')>" % self.risk_name, self.ratio, self.description


class Pilot(Base):
    """
    The pilot table stores the information about the Pilots in a defined locations and what users are participating
    """

    __tablename__ = 'pilot'

    id = Column(Integer, Sequence('pilot_id_seq'), primary_key=True)
    name = Column(String(50))
    population_size = Column(BigInteger)
    # One2Many
    user_in_role = relationship('UserInRole')
    # Fkeys
    location_id = Column(Integer, ForeignKey('location.id'))

    def __repr__(self):
        return "<Pilot(name='%s', population_size='%s')>" % (self.name, self.population_size)


class User(Base):
    """
    This table allows to store all related data from User who makes the executed_action
    """

    __tablename__ = 'user'

    id = Column(String(75), primary_key=True)
    # m2m
    action = relationship("ExecutedAction")

    def __repr__(self):
        return "<User(id='%s')>" % self.id


# Todo we need to build profile with openSHR and registed with  created_date = Column(DateTime, default=datetime.datetime.utcnow)