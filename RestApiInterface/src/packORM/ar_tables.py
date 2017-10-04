# -*- coding: utf-8 -*-

"""
This file uses SQL alchemy declarative base model to create SQL Tables.

Here we define tables, relationships between tables and so on.

"""

import ConfigParser
import datetime
import inspect
import os
import arrow
from sqlalchemy_utils import ArrowType

from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from sqlalchemy import Column, Integer, String, Boolean, Sequence, Float, BigInteger, ForeignKey, Numeric, \
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

    User - CDAction -- Activity -- Location
    """

    __tablename__ = 'executed_action'
    # __searchable__ = ['acquisition_datetime']


    # Generating the Sequence
    executed_action_id_seq = Sequence('executed_action_id_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=executed_action_id_seq.next_value(), primary_key=True)
    # Associated information
    acquisition_datetime = Column(ArrowType(timezone=True), default=arrow.utcnow())  # Time of item registered in db
    execution_datetime = Column(ArrowType(timezone=True))  # Time of registered action
    rating = Column(Numeric(precision=5, scale=2))
    sensor_id = Column(Integer)
    position = Column(String(25))
    data_source_type = Column(String(1000))  # An "array" containing the data source
    extra_information = Column(String(1000))  # An "array" containing extra information

    # FK keys
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'))
    cd_action_id = Column(Integer, ForeignKey('cd_action.id'))
    location_id = Column(Integer, ForeignKey('location.id'))

    # Relationship with other TABLES
    cd_action = relationship("CDAction")
    location = relationship("Location")

    def __repr__(self):
        return "<ExecutedAction(id='%s', acquisition_datetime='%s', execution_datetime='%s', " \
               "rating='%s')>" % (self.id, self.acquisition_datetime, self.execution_datetime, self.rating)


# TODO in this table it is importat to define better the location fields.

class ExecutedActivity(Base):
    """
    Multi relationship table

    User - CDActivity - Location
    """

    __tablename__ = 'executed_activity'
    # __searchable__ = ['data_source_type', 'start_time', 'end_time', 'duration']

    # Generating the Sequence
    executed_activity_id_seq = Sequence('executed_activity_id_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=executed_activity_id_seq.next_value(), primary_key=True)
    start_time = Column(ArrowType(timezone=True),
                        nullable=False)  # These two fields are calculated thought executed action
    end_time = Column(ArrowType(timezone=True), nullable=False)
    duration = Column(Integer, nullable=True)
    data_source_type = Column(String(200))

    # FK keys
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'))
    cd_activity_id = Column(Integer, ForeignKey('cd_activity.id'), nullable=True)

    # Relationship with other tables
    executed_activity_executed_action_rel = relationship("ExecutedActivityExecutedActionRel",
                                                         cascade="all, delete-orphan")

    cd_location_type_executed_activity_rel = relationship("CDLocationTypeExecutedActivityRel",
                                                          cascade="all, delete-orphan")

    def __repr__(self):
        return "<ExecutedActivity(id='%s', start_time='%s', end_time='%s', duration='%s')>" % (self.id,
                                                                                               self.start_time,
                                                                                               self.end_time,
                                                                                               self.duration)


class ExecutedTransformedAction(Base):
    """
    Multi relationship table

    USER - CDTransformedAction - CDEAM
    """

    __tablename__ = 'executed_transformed_action'

    # Generating the Sequence
    executed_activity_id_seq = Sequence('executed_activity_id_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=executed_activity_id_seq.next_value(), primary_key=True)
    transformed_acquisition_datetime = Column(ArrowType(timezone=True), default=arrow.utcnow())
    transformed_execution_datetime = Column(ArrowType(timezone=True))

    # FK keys
    executed_action_id = Column(Integer, ForeignKey('executed_action.id'), nullable=True)
    cd_transformed_action_id = Column(Integer, ForeignKey('cd_transformed_action.id'))
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'))

    # Relationships with other tables
    cd_transformed_action = relationship('CDTransformedAction')
    executed_action = relationship('ExecutedAction')

    def __repr__(self):
        return "<ExecutedTransformedAction(id='%s', transformed_acquisition_datetime='%s', " \
               "transformed_execution_datetime='%s')>" % (self.id, self.transformed_acquisition_datetime,
                                                          self.transformed_execution_datetime)


class UserInEAM(Base):
    """
    Multi relationship table

    User -- CDActivity -- CDEAM
    """

    __tablename__ = 'user_in_eam'

    cd_activity_id = Column(Integer, ForeignKey('cd_activity.id'), primary_key=True)
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'), primary_key=True)
    cd_eam_id = Column(Integer, ForeignKey('cd_eam.id'), primary_key=True)
    date = Column(ArrowType(timezone=True), default=arrow.utcnow(), nullable=True)

    # Relationship with other tables
    cd_eam = relationship('CDEAM')
    cd_activity = relationship('CDActivity')

    def __repr__(self):
        return "<UserInEAM(cd_activity_id='%s', user_in_role_id='%s', " \
               "cd_eam_id='%s', date='%s')>" % (self.cd_activity_id, self.user_in_role_id, self.cd_eam_id, self.date)


class ExecutedActivityExecutedActionRel(Base):
    """
    ExecutedActivity < -- > ExecutedAction
    """

    __tablename__ = 'executed_activity_executed_action_rel'

    executed_activity_id = Column(Integer, ForeignKey('executed_activity.id'), primary_key=True)
    executed_action_id = Column(Integer, ForeignKey('executed_action.id'), primary_key=True)
    executed_action = relationship('ExecutedAction')


class CDEAMStartRangeRel(Base):
    """
    CDEAM < -- > StartRange
    """

    __tablename__ = 'cd_eam_start_range_rel'

    cd_eam_id = Column(Integer, ForeignKey('cd_eam.id'), primary_key=True)
    start_range_id = Column(Integer, ForeignKey('start_range.id'), primary_key=True)
    start_range = relationship("StartRange")


class CDEAMCDTransformedActionRel(Base):
    """
    CDEAM < -- > CDTransformedAction
    """

    __tablename__ = 'cd_eam_cd_transformed_action_rel'

    cd_eam_id = Column(Integer, ForeignKey('cd_eam.id'), primary_key=True)
    cd_transformed_action_id = Column(Integer, ForeignKey('cd_transformed_action.id'), primary_key=True)
    transformed_action = relationship("CDTransformedAction")


class CDEAMLocationRel(Base):
    """
    CDEAM < -- > Location

    """

    __tablename__ = 'cd_eam_location_rel'

    cd_eam_id = Column(Integer, ForeignKey('cd_eam.id'), primary_key=True)
    location_id = Column(Integer, ForeignKey('location.id'), primary_key=True)
    location = relationship('Location')


class CDEAMUserInRoleRel(Base):
    """
    CDEAM < -- > UserInRole
    """

    __tablename__ = 'cd_eam_user_in_role_rel'

    cd_eam_id = Column(Integer, ForeignKey('cd_eam.id'), primary_key=True)
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'), primary_key=True)
    user_in_role = relationship('UserInRole')


class CDLocationTypeExecutedActivityRel(Base):
    """
    ExecutedActivity < -- > Location
    """

    __tablename__ = 'cd_location_type_executed_activity_rel'

    cd_location_type_id = Column(Integer, ForeignKey('cd_location_type.id'), primary_key=True)
    executed_activity_id = Column(Integer, ForeignKey('executed_activity.id'), primary_key=True)
    house_number = Column(Integer)
    executed_activity = relationship("CDLocationType")


class LocationCDLocationTypeRel(Base):
    """
    Location < -- > LocationType
    """

    __tablename__ = 'location_cd_location_type_rel'

    location_id = Column(Integer, ForeignKey('location.id'), primary_key=True)
    location_type_id = Column(Integer, ForeignKey('cd_location_type.id'), primary_key=True)
    parent_location_type_id = Column(Integer, ForeignKey('cd_location_type.id'))

    # Relationship
    location = relationship('Location')

# Rename to payload_value
class PayloadValue(Base):
    """
    Metric < -- > CDAction
    """

    __tablename__ = 'payload_value'

    cd_metric_id = Column(Integer, ForeignKey('cd_metric.id'), primary_key=True)
    cd_action_id = Column(Integer, ForeignKey('cd_action.id'), primary_key=True)
    acquisition_datetime = Column(ArrowType(timezone=True), primary_key=True)  # Same as executed_action registered time
    execution_datetime = Column(ArrowType(timezone=True), nullable=False)
    value = Column(String(50), nullable=False)
    cd_action = relationship('CDAction')


# Basic Tables
class UserInRole(Base):
    """
    This table allows to store all related data from User who makes the executed_action
    """

    __tablename__ = 'user_in_role'
    # __searchable__ = ['pilot_source_user_id']

    # Generating the Sequence
    user_in_role_seq = Sequence('user_in_role_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=user_in_role_seq.next_value(), primary_key=True)
    valid_from = Column(ArrowType(timezone=True), default=arrow.utcnow())
    valid_to = Column(ArrowType(timezone=True))
    pilot_source_user_id = Column(String(20))

    # one2many
    user_in_system_id = Column(Integer, ForeignKey('user_in_system.id'))
    cd_role_id = Column(Integer, ForeignKey('cd_role.id'))
    pilot_code = Column(String(4), ForeignKey('pilot.pilot_code'))

    # m2m
    action = relationship("ExecutedAction", cascade="all, delete-orphan")
    executed_activity = relationship("ExecutedActivity", cascade="all, delete-orphan")
    executed_transformed_action = relationship("ExecutedTransformedAction", cascade="all, delete-orphan")
    user_in_eam = relationship("UserInEAM", cascade="all, delete-orphan")

    def __repr__(self):
        return "<UserInRole(id='%s', valid_from='%s'. valid_to='%s')>" % (self.id, self.valid_from, self.valid_to)


class UserInSystem(Base):
    """
    Base data of the users
    """
    __tablename__ = 'user_in_system'

    # Generating the Sequence
    user_in_system_seq = Sequence('user_in_system_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=user_in_system_seq.next_value(), primary_key=True)
    username = Column(String(25), nullable=False, unique=True)
    password = Column(Password(rounds=13), nullable=False)
    display_name = Column(String(100))
    created_date = Column(ArrowType(timezone=True), default=arrow.utcnow())

    # one2many
    user_action = relationship('UserAction')
    user_in_role = relationship('UserInRole')

    def __repr__(self):
        return "<UserInSystem(username='%s', password='%s', created_date='%s')>" % (
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


class CDAction(Base):
    """
    Action registration
    """
    __tablename__ = 'cd_action'
    #__searchable__ = ['action_name']

    # Generating the Sequence
    cd_action_id_seq = Sequence('cd_action_id_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=cd_action_id_seq.next_value(), primary_key=True)
    action_name = Column(String(50), unique=True)
    action_category = Column(String(25))
    action_description = Column(String(250), nullable=False)

    def __repr__(self):
        return "<CDAction(action_name='%s', action_category='%s', action_description='%s')>" % \
               (self.action_name, self.action_description, self.action_category)


class Location(Base):
    """
    Users location in a specific time
    """

    __tablename__ = 'location'
    #__searchable__ = ['location_name']

    # Generating the Sequence
    location_id_seq = Sequence('location_id_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=location_id_seq.next_value(), primary_key=True)
    location_name = Column(String(500), unique=True, nullable=False)
    indoor = Column(Boolean)
    # One2Many
    pilot_code = Column(String(4), ForeignKey('pilot.pilot_code'), nullable=True)

    def __repr__(self):
        return "<Location(location_name='%s', indoor='%s')>" % (
            self.location_name, self.indoor)


class CDLocationType(Base):
    """
    Each location has a location type to have a logical order in the system
    """

    __tablename__ = 'cd_location_type'

    # Generating the Sequence
    location_type_id_seq = Sequence('location_type_id_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=location_type_id_seq.next_value(), primary_key=True)
    location_type_name = Column(String(50), unique=True)

    # one2many relations (Multiple)
    location_location_type_rel = relationship("LocationCDLocationTypeRel",
                                              foreign_keys='LocationCDLocationTypeRel.location_type_id')
    parent_location_location_type_rel = relationship("LocationCDLocationTypeRel",
                                                     foreign_keys='LocationCDLocationTypeRel.parent_location_type_id')


class CDActivity(Base):
    """
    CDActivity contains the codebook of possible Activities in the project.

    An activity is set of different performed actions:

        --> Open the fridge
        --> Put the milk in the bowl
        --> .....

    """

    __tablename__ = 'cd_activity'
    #__searchable__ = ['activity_name']

    # Generating the Sequence
    activity_id_seq = Sequence('cd_activity_id_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=activity_id_seq.next_value(), primary_key=True)
    activity_name = Column(String(50), unique=True)
    activity_description = Column(String(200), nullable=True)
    creation_date = Column(ArrowType(timezone=True), default=arrow.utcnow())
    instrumental = Column(Boolean, default=False, nullable=False)  # Default value set to False --> Normal Activities

    # One2one
    # user_in_eam = relationship("UserInEAM", uselist=False, back_populates="cd_activity")

    # One2Many
    executed_activity = relationship("ExecutedActivity", cascade="all, delete-orphan")

    # one2many
    # expected_inter_behaviour = relationship("InterBehaviour", foreign_keys='InterBehaviour.expected_activity_id')
    # real_inter_behaviour = relationship("InterBehaviour", foreign_keys='InterBehaviour.real_activity_id')

    def __repr__(self):
        return "<CDActivity(activity_name='%s')>" % self.activity_name


class Pilot(Base):
    """
    The pilot table stores the information about the Pilots in a defined locations and what users are participating
    """

    __tablename__ = 'pilot'
    #__searchable__ = ['pilot_name']

    pilot_code = Column(String(3), unique=True, nullable=False, primary_key=True)
    pilot_name = Column(String(50), unique=True, nullable=False)
    population_size = Column(BigInteger)
    # One2Many
    user_in_role = relationship('UserInRole')
    location = relationship('Location')

    def __repr__(self):
        return "<Pilot(pilot_code='%s', pilot_name='%s', population_size='%s')>" % \
               (self.pilot_code, self.pilot_name, self.population_size)


class Stakeholder(Base):
    """
    Each role can be a part of a stakeholder type, this class allows to create different kind of
    user groups.
    """

    __tablename__ = 'stakeholder'

    abbreviation = Column(String(3), primary_key=True)
    stakeholder_name = Column(String(100), nullable=False)
    stakeholder_description = Column(String(250))
    valid_from = Column(ArrowType(timezone=True), default=arrow.utcnow())
    valid_to = Column(ArrowType(timezone=True), nullable=True)

    # One2many relationship
    cd_role = relationship('CDRole')

    def __repr__(self):
        return "<Stakeholder(abbreviation='%s', stakeholder_name='%s', stakeholder_description='%s', " \
               "valid_from='%s', valid_to='%s')>" % (self.abbreviation, self.stakeholder_name,
                                                     self.stakeholder_description,
                                                     self.valid_from, self.valid_to)


class CDRole(Base):
    """
    This table stores all data related to the roles for users in the system. The idea is to stablish a role-access
    level entry points to limit user iterations int he system.
    """

    __tablename__ = 'cd_role'
    # __searchable__ = ['role_name']

    # Generating the Sequence
    cd_role_seq = Sequence('cd_role_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=cd_role_seq.next_value(), primary_key=True)
    role_name = Column(String(50), nullable=False, unique=True)
    role_abbreviation = Column(String(3))
    role_description = Column(String(350), nullable=True)
    valid_from = Column(ArrowType(timezone=True), default=arrow.utcnow())
    valid_to = Column(ArrowType(timezone=True), nullable=True)

    # FK's
    stakeholder_abbreviation = Column(String(3), ForeignKey('stakeholder.abbreviation'))

    # one2many
    user_in_role = relationship('UserInRole')

    def __repr__(self):
        return "<CDRole(id='%s', role_name='%s', role_abbreviation='%s', role_description='%s'," \
               "valid_from='%s', valid_to='%s')>" % (self.id, self.role_name,
                                                     self.role_abbreviation, self.role_description, self.valid_from,
                                                     self.valid_to)

class CDEAM(Base):
    """
    This table stores the duration of each related action/activity in a location
    """

    __tablename__ = 'cd_eam'

    # Generating the Sequence
    cd_eam_seq = Sequence('cd_eam_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=cd_eam_seq.next_value(), primary_key=True)
    duration = Column(Integer)
    creation_date = Column(ArrowType(timezone=True), default=arrow.utcnow())
    # one2one

    # activity_id = Column(Integer, ForeignKey('activity.id'))
    # activity = relationship("Activity", back_populates="cd_eam")

    # many2many
    start_range = relationship("CDEAMStartRangeRel")
    cd_transformed_action = relationship("CDEAMCDTransformedActionRel")
    location = relationship("CDEAMLocationRel")
    user_in_role = relationship("CDEAMUserInRoleRel")

    def __repr__(self):
        return "<EAM(duration='%s')>" % self.duration


class StartRange(Base):
    """
    This table defines some ranges of dates to store what is start time and end time of each
    EAM performed by each user.
    """

    __tablename__ = 'start_range'

    # Generating the Sequence
    start_range_seq = Sequence('start_range_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=start_range_seq.next_value(), primary_key=True)
    start_time = Column(String(10))
    end_time = Column(String(10))

    def __repr__(self):
        return "<StartRange(start_time='%s', end_time='%s')>" % (self.start_time, self.end_time)


class UserAction(Base):
    """
    This table stores all user actions in DB. Each user has its historical data stored to study its actions in the
    system. The idea is to have some reference in case of security breach.
    """

    __tablename__ = 'user_action'

    # Generating the Sequence
    user_action_seq = Sequence('user_action_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=user_action_seq.next_value(), primary_key=True)
    route = Column(String(25))
    data = Column(String(255))
    ip = Column(String(60))
    agent = Column(String(255))
    date = Column(ArrowType(timezone=True), default=arrow.utcnow())
    status_code = Column(Integer)
    # One2Many
    user_in_system_id = Column(Integer, ForeignKey('user_in_system.id'))

    def __repr__(self):
        return "<UserAction(route='%s', data='%s', ip='%s', agent='%s', date='%s', satus_code='%s')>" % (
            self.route, self.date, self.ip, self.agent, self.date, self.status_code)


class CDMetric(Base):
    """
    Some actions has a random valued metrics. This metrics are an extra information that can be used for different
    purposes. This table record each different metric in the sytem.

    """

    __tablename__ = 'cd_metric'

    # Generating the Sequence
    cd_metric_seq = Sequence('cd_metric_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=cd_metric_seq.next_value(), primary_key=True)
    metric_name = Column(String(50), nullable=False)
    metric_description = Column(String(255), nullable=True)
    metric_base_unit = Column(String(50), nullable=True)
    # M2M relationship
    payload_value = relationship('PayloadValue')


class CDTransformedAction(Base):
    """
    This table is used to convert the executed actions of a user to EAM readable actions that can be used to infer
    new activities.
    """

    __tablename__ = 'cd_transformed_action'
    #__searchable__ = ['transformed_action_name']

    # Generating the Sequence
    cd_transformed_action_seq = Sequence('cd_transformed_action_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=cd_transformed_action_seq.next_value(), primary_key=True)
    transformed_action_name = Column(String(255), unique=True)
    transformed_action_description = Column(String(255), nullable=True)
