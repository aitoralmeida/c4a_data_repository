# -*- coding: utf-8 -*-

"""
This file uses SQL alchemy declarative base model to create SQL Tables.

Here we define tables, relationships between tables and so on.

"""

import ConfigParser
import datetime
import inspect
import os

from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from sqlalchemy import Column, Integer, String, Boolean, Sequence, Float, BigInteger, ForeignKey, TIMESTAMP, \
    Text, TypeDecorator, event, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.schema import CreateSchema

from PasswordHash import PasswordHash
from Encryption import Encryption

__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


DEFAULT_KEY = '2070711C879178C93CD3DB09FC4EADC6'

# Key encryption configuration
config = ConfigParser.ConfigParser()
# Checks actual path of the file and sets config file.
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
config_dir = os.path.abspath(current_dir + '../../../conf/rest_api.cfg')
config.read(config_dir)

# Loading saved key or defaulting to one
if 'security' in config.sections():
    cipher_key = config.get('security', 'encryption_key') or DEFAULT_KEY
else:
    # Using a default code key
    cipher_key = DEFAULT_KEY

# Global variable declarative base
Base = declarative_base(metadata=MetaData(schema='city4age_ar'))


class EncryptedValue(TypeDecorator):
    """
    Allows storing sensible data into database in an hybrid encrypted environment

    This definition is used as following:

    table_column = Column(EncryptedValue(key), nullable=False, unique=True)

    """
    impl = Text

    def __init__(self, p_cipher_key, **kwds):
        self.cipher_key = p_cipher_key
        super(EncryptedValue, self).__init__(**kwds)

    def process_bind_param(self, value, dialect):
        return self._convert(value).value

    def process_result_value(self, value, dialect):
        if value is not None:
            return Encryption(value, cipher_key)

    def validator(self, value):
        """Provides a validator/converter for @validates usage.

        For example, once you defined the values to be encrypted in your Table use:

        @validates('password')
        def _validate_password(self, cipher_key, password):
            return getattr(type(self), cipher_key).type.validator(password)

        It is strongly recommended to use this validator to know exactly
        if data is creating well into database.
        """
        return self._convert(value)

    def _convert(self, value):
        """Returns a Encryption object from the given string.

        PasswordHash instances or None values will return unchanged.
        Strings will be hashed and the resulting PasswordHash returned.
        Any other input will result in a TypeError.
        """
        if isinstance(value, Encryption):
            return value
        elif isinstance(value, basestring):
            return Encryption.new(value, self.cipher_key)
        elif value is not None:
            raise TypeError(
                'Cannot convert {} to a EncryptedValue'.format(type(value)))


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
    # Create schema if it is necessary
    q = p_engine.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'city4age_ar';")
    if q.rowcount == 0:
        event.listen(Base.metadata, 'before_create', CreateSchema('city4age_ar'))
    return Base.metadata.create_all(p_engine)


# Association tables for m2m Relationships
class ExecutedAction(Base):
    """
    Multi relationship table.

    User - Action -- Activity -- Location
    """

    __tablename__ = 'executed_action'

    id = Column(Integer, Sequence('executed_action_id_seq'), primary_key=True)
    user_in_role_id = Column(String(75), ForeignKey('user_in_role.id'))
    action_id = Column(Integer, ForeignKey('action.id'))
    activity_id = Column(Integer, ForeignKey('activity.id'), nullable=True)
    location_id = Column(Integer, ForeignKey('location.id'))
    date = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    executed_action_date = Column(TIMESTAMP)
    # Asociated information
    rating = Column(Integer)
    sensor_id = Column(Integer)
    instance_id = Column(String(4))
    extra_information = Column(Text)

    # Relationship with other TABLES
    action = relationship("Action")
    activity = relationship("Activity")
    location = relationship("Location")


class EAMStartRangeRel(Base):
    """
    EAM < -- > StartRange
    """

    __tablename__ = 'eam_start_range_rel'

    eam_id = Column(Integer, ForeignKey('eam.id'), primary_key=True)
    start_range_id = Column(Integer, ForeignKey('start_range.id'), primary_key=True)
    start_range = relationship("StartRange")


class EAMSimpleLocationRel(Base):
    """
    EAM < -- > SimpleLocation
    """

    __tablename__ = 'eam_simple_location_rel'

    eam_id = Column(Integer, ForeignKey('eam.id'), primary_key=True)
    simple_location_id = Column(Integer, ForeignKey('simple_location.id'), primary_key=True)
    simple_location = relationship("SimpleLocation")


class LocationActivityRel(Base):
    """
    Activity < -- > Location
    """

    __tablename__ = 'location_activity_rel'

    location_id = Column(Integer, ForeignKey('location.id'), primary_key=True)
    activity_id = Column(Integer, ForeignKey('activity.id'), primary_key=True)
    house_number = Column(Integer)
    activity = relationship("Activity")


class ActionValue(Base):
    """
    Metric < -- > Action
    """

    __tablename__ = 'action_value'

    metric_id = Column(Integer, ForeignKey('metric.id'), primary_key=True)
    action_id = Column(Integer, ForeignKey('action.id'), primary_key=True)
    date = Column(TIMESTAMP, primary_key=True)
    value = Column(String(10), nullable=False)
    action = relationship('Action')

# Tables
class UserInRole(Base):
    """
    This table allows to store all related data from User who makes the executed_action
    """

    __tablename__ = 'user_in_role'

    id = Column(String(75), primary_key=True)
    valid_from = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    valid_to = Column(TIMESTAMP)
    medical_record = Column(String(75))

    # one2many
    #stake_holder_name = Column(String(25), ForeignKey('stake_holder.name'))
    user_registered_id = Column(Integer, ForeignKey('user_registered.id'))
    cd_role_id = Column(Integer, ForeignKey('cd_role.id'))
    pilot_name = Column(String(50), ForeignKey('pilot.name'))

    # m2m
    action = relationship("ExecutedAction", cascade="all, delete-orphan")

    def __repr__(self):
        return "<User(id='%s', valid_from='%s'. valid_to='%s')>" % (self.id, self.valid_from, self.valid_to)


class UserRegistered(Base):
    """
    Base data of the users
    """
    __tablename__ = 'user_registered'

    id = Column(Integer, Sequence('user_registered_seq'), primary_key=True)
    username = Column(Text, nullable=False, unique=True)
    password = Column(Password(rounds=13), nullable=False)
    # Or specify a cost factor other than the default 13
    # password = Column(Password(rounds=10))
    # Without rounds System will use 13 rounds by default
    created_date = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    # one2many
    user_action = relationship('UserAction')
    user_in_role = relationship('UserInRole')

    def __repr__(self):
        return "<UserRegistered(username='%s', password='%s', created_date='%s')>" % (
            self.username, self.password, self.created_date)

    def to_json(self):
        return dict(username=self.username,
                    password=self.password,
                    created_date=self.created_date)

    # Password Encryption validation
    @validates('password')
    def _validate_password(self, key, password):
        return getattr(type(self), key).type.validator(password)

    # Token management
    def generate_auth_token(self, app, expiration=600):
        """
        This method generates a new auth token to the user.

        :param app: Flask application Object
        :param expiration: Expiration time of the token

        :return: A string with the token.
        """
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token, app):
        """
        This method verify user's token

        :param token: Token information
        :param app: Flask application Object

        :return: User ID
        """
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        return data


class Action(Base):
    """
    Action registration
    """
    __tablename__ = 'action'

    id = Column(Integer, Sequence('action_id_seq'), primary_key=True)
    action_name = Column(String(50))
    category = Column(String(25))

    # one2many
    eam = relationship("EAM")

    def __repr__(self):
        return "<Action(action_name='%s', category='%s')>" % (
            self.action_name, self.category)


class Location(Base):
    """
    Users location in a specific time
    """
    __tablename__ = 'location'

    id = Column(Integer, Sequence('location_id_seq'), primary_key=True)
    # The location could be a URN based location or a combination of latitude and longitude
    urn = Column(String(75))
    latitude = Column(String(15))
    longitude = Column(String(15))
    indoor = Column(Boolean)
    # One2Many
    pilot_name = Column(String(50), ForeignKey('pilot.name'), nullable=True)

    # many2many
    activity = relationship("LocationActivityRel")

    def __repr__(self):
        return "<Location(location_name='%s', indoor='%s', urn='%s', latitude='%s', longitude='%s')>" % (
            self.location_name, self.indoor, self.urn, self.latitude, self.longitude)


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
    activity_start_date = Column(TIMESTAMP)
    activity_end_date = Column(TIMESTAMP)
    creation_date = Column(TIMESTAMP, default=datetime.datetime.utcnow)         # get current date
    since = Column(TIMESTAMP, nullable=True)

    # One2one
    eam = relationship("EAM", uselist=False, back_populates="activity")

    # one2many
    expected_inter_behaviour = relationship("InterBehaviour", foreign_keys='InterBehaviour.expected_activity_id')
    real_inter_behaviour = relationship("InterBehaviour", foreign_keys='InterBehaviour.real_activity_id')

    def __repr__(self):
        return "<Activity(activity_name='%s')>" % self.activity_name


class Pilot(Base):
    """
    The pilot table stores the information about the Pilots in a defined locations and what users are participating
    """

    __tablename__ = 'pilot'

    name = Column(String(50), primary_key=True)
    pilot_code = Column(String(4), unique=True, nullable=False)
    population_size = Column(BigInteger)
    # One2Many
    user_in_role = relationship('UserInRole')
    location = relationship('Location')

    def __repr__(self):
        return "<Pilot(name='%s', pilot_code='%s', population_size='%s')>" % (self.name, self.pilot_code,
                                                                              self.population_size)


class CDRole(Base):
    """
    This table stores all data related to the roles for users in the system. The idea is to stablish a role-access
    level entry points to limit user iterations int he system.
    """

    __tablename__ = 'cd_role'

    id = Column(Integer, Sequence('cd_role_seq'), primary_key=True)
    role_name = Column(String(50), nullable=False, unique=True)
    role_abbreviation = Column(String(3), nullable=False)
    role_description = Column(String(350), nullable=False)
    valid_from = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    valid_to = Column(TIMESTAMP)

    # one2many
    user_in_role = relationship('UserInRole')

    def __repr__(self):
        return "<CDRole(id='%s', role_name='%s', role_abbreviation='%s', role_description='%s'," \
               "valid_from='%s', valid_to='%s')>" % (self.id, self.role_name,
                                                     self.role_abbreviation, self.role_description, self.valid_from,
                                                     self.valid_to)


class InterBehaviour(Base):
    """
    This table contains all data related to InterBehaviours. Here we are going to store some data about what is
    expected activity. What is the real activity and what is the deviation value.
    """

    __tablename__ = 'inter_behaviour'

    id = Column(Integer, Sequence('inter_behaviour_seq'), primary_key=True)
    deviation = Column(Float(10))
    # many2one relationships
    expected_activity_id = Column(Integer, ForeignKey('activity.id'))
    real_activity_id = Column(Integer, ForeignKey('activity.id'))

    def __repr__(self):
        return "<InterBehaviour(deviation='%s')>" % self.deviation


# EAM Related Tables
class EAM(Base):
    """
    This table stores the duration of each related action/activity in a simple place.
    """

    __tablename__ = 'eam'

    id = Column(Integer, Sequence('eam_seq'), primary_key=True)
    duration = Column(Integer)
    #one2one
    activity_id = Column(Integer, ForeignKey('activity.id'))
    activity = relationship("Activity", back_populates="eam")
    # one2many
    action_id = Column(Integer, ForeignKey('action.id'))
    # many2many
    start_range = relationship("EAMStartRangeRel")
    simple_location = relationship("EAMSimpleLocationRel")

    def __repr__(self):
        return "<EAM(duration='%s')>" % self.duration


class SimpleLocation(Base):
    """
    This table defines a list of simple locations. For example:

    "Kitchen", "Bathroom", "Restroom"......

    """

    __tablename__ = 'simple_location'

    id = Column(Integer, Sequence('simple_location_seq'), primary_key=True)
    simple_location_name = Column(String(25), unique=True)

    def __repr__(self):
        return "<SimpleLocation(simple_location_name='%s')>" % self.simple_location_name


class StartRange(Base):
    """
    This table defines some ranges of dates to store what is start time and end time of each
    EAM performed by each user.
    """

    __tablename__ = 'start_range'

    id = Column(Integer, Sequence('start_range_seq'), primary_key=True)
    start_hour = Column(TIMESTAMP)
    end_hour = Column(TIMESTAMP)

    def __repr__(self):
        return "<SimpleLocation(start_hour='%s', end_hour='%s')>" % (self.start_hour, self.end_hour)


class UserAction(Base):
    """
    This table stores all user actions in DB. Each user has its historical data stored to study its actions in the
    system. The idea is to have some reference in case of security breach.
    """

    __tablename__ = 'user_action'

    id = Column(Integer, Sequence('user_action_seq'), primary_key=True)
    route = Column(String(25))
    data = Column(String(255))
    ip = Column(String(60))
    agent = Column(String(255))
    date = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    status_code = Column(Integer)

    # One2Many
    user_registered_id = Column(Integer, ForeignKey('user_registered.id'))


class Metric(Base):
    """
    Some actions has a random valued metrics. This metrics are an extra information that can be used for different
    purposes. This table record each different metric in the sytem.

    """

    __tablename__ = 'metric'

    id = Column(Integer, Sequence('metric_seq'), primary_key=True)
    name = Column(String(10))
    description = Column(String(255), nullable=True)
    # M2M relationship
    action_value = relationship('ActionValue')
