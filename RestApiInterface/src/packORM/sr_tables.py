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

from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from sqlalchemy import Column, Integer, String, Boolean, Sequence, Numeric, Float, BigInteger, ForeignKey, \
    LargeBinary, TIMESTAMP, Text, TypeDecorator, event, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.schema import CreateSchema
from sqlalchemy_utils import ArrowType

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
Base = declarative_base(metadata=MetaData(schema='city4age_sr'))

"""
Definition of table special types. Here I defined some special tables for table encryption and password hashing.
"""


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
    q = p_engine.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'city4age_sr';")
    if q.rowcount == 0:
        event.listen(Base.metadata, 'before_create', CreateSchema('city4age_sr'))
    return Base.metadata.create_all(p_engine)


"""
Definition of each different tables.

Here, is defined all table logic of the system based in Shared Repository database schema.

This part of the file is divided into:

    --> Intermediate tables: Middle tables generated by ManyToMany relationships
    --> Base tables: Basic tables created by entities.

"""

# Intermediate tables
"""
Intermediate tables. Here I will to define each intermediate table.
"""


class FrailtyStatusTimeline(Base):
    """
    Multiple relationship intermediate table

    user_in_role -- time_interval -- cd_frailty_status
    """

    __tablename__ = 'frailty_status_timeline'

    time_interval_id = Column(Integer, ForeignKey('time_interval.id'), primary_key=True)
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'), primary_key=True)
    changed = Column(ArrowType(timezone=True), default=arrow.utcnow(), primary_key=True)

    # Data
    frailty_notice = Column(String(200))

    # FK
    changed_by = Column(Integer, ForeignKey('user_in_role.id'), nullable=False)
    frailty_status = Column(String(9), ForeignKey('cd_frailty_status.frailty_status'), nullable=False)

    # Relationships
    time_interval = relationship('TimeInterval')
    cd_frailty_status = relationship('CDFrailtyStatus')


class CDPilotDetectionVariable(Base):
    """
    Pilot < -- > CDDetectionVariable
    """

    __tablename__ = 'cd_pilot_detection_variable'

    pilot_code = Column(String(50), ForeignKey('pilot.code'), primary_key=True)
    detection_variable_id = Column(Integer, ForeignKey('cd_detection_variable.id'), primary_key=True)

    # Data
    detection_variable_description_formula = Column(String(255))

    # Relationship with other Tables
    cd_detection_variable = relationship('CDDetectionVariable')


class AssessedGefValueSet(Base):
    """
    GeriatricFactorValue < -- > Assessment
    """

    __tablename__ = 'assessed_gef_value_set'

    gef_value_id = Column(Integer, ForeignKey('geriatric_factor_value.id'), primary_key=True)
    assessment_id = Column(Integer, ForeignKey('assessment.id'), ForeignKey('assessment.id'), primary_key=True)

    # Relationship with other Tables
    assessment = relationship('Assessment')


class AssessmentAudienceRole(Base):
    """
    cd_role <--> assessment
    """

    __tablename__ = 'assessment_audience_role'

    assessment_id = Column(Integer, ForeignKey('assessment.id'), primary_key=True)
    role_id = Column(Integer, ForeignKey('cd_role.id'), primary_key=True)
    assigned = Column(ArrowType(timezone=True), default=arrow.utcnow(), nullable=True)

    # Relationship with other Tables
    assessment = relationship('Assessment')


class ExecutedAction(Base):
    """
    Multi relationship table.

    User - CDAction -- Activity -- Location
    """

    __tablename__ = 'executed_action'

    # Generating the Sequence
    executed_action_id_seq = Sequence('executed_action_id_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=executed_action_id_seq.next_value(), primary_key=True)
    # Associated information
    acquisition_datetime = Column(ArrowType(timezone=True), default=arrow.utcnow())
    execution_datetime = Column(ArrowType(timezone=True))
    rating = Column(Numeric(precision=5, scale=2))
    sensor_id = Column(Integer)
    position = Column(String(255))
    data_source_type = Column(String(200))  # An "array" containing the data source
    extra_information = Column(String(1000))  # An "array" containing extra information

    # FK keys
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'))
    cd_action_id = Column(Integer, ForeignKey('cd_action.id'))
    activity_id = Column(Integer, ForeignKey('activity.id'), nullable=True)
    location_id = Column(Integer, ForeignKey('location.id'))

    # Relationship with other TABLES
    cd_action = relationship("CDAction")
    activity = relationship("Activity")
    location = relationship("Location")


class LocationLocationTypeRel(Base):
    """
    Location < -- > LocationType
    """

    __tablename__ = 'location_location_type_rel'

    location_id = Column(Integer, ForeignKey('location.id'), primary_key=True)
    location_type_id = Column(Integer, ForeignKey('location_type.id'), primary_key=True)
    location_type = relationship('LocationType')


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


class LocationActivityRel(Base):
    """
    Activity < -- > Location
    """

    __tablename__ = 'location_activity_rel'

    location_id = Column(Integer, ForeignKey('location.id'), primary_key=True)
    activity_id = Column(Integer, ForeignKey('activity.id'), primary_key=True)
    house_number = Column(Integer)
    activity = relationship("Activity")

class CDActionMetric(Base):
    """
    Metric < -- > CDAction
    """

    __tablename__ = 'cd_action_metric'

    metric_id = Column(Integer, ForeignKey('metric.id'), primary_key=True)
    cd_action_id = Column(Integer, ForeignKey('cd_action.id'), primary_key=True)
    date = Column(ArrowType(timezone=True), primary_key=True, default=arrow.utcnow())
    execution_datetime = Column(ArrowType(timezone=True), nullable=False)
    value = Column(String(50), nullable=False)
    cd_action = relationship('CDAction')


"""
Base tables. Here is defined the basic tables.
"""


class CDRole(Base):
    """
    This table contains information about the roles of the system. It stores the role information and its
    validity in the system
    """

    __tablename__ = 'cd_role'

    # Generating the Sequence
    cd_role_seq = Sequence('cd_role_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=cd_role_seq.next_value(), primary_key=True)
    role_name = Column(String(50), nullable=False, unique=True)
    role_abbreviation = Column(String(3))
    role_description = Column(String(350), nullable=True)
    valid_from = Column(ArrowType(timezone=True), default=arrow.utcnow())
    valid_to = Column(ArrowType(timezone=True), nullable=True)

    # One2Many
    user_in_role = relationship('UserInRole')

    # Many2One
    stakeholder_abbreviation = Column(String(3), ForeignKey('stakeholder.abbreviation'))

    # M2M Relationship
    assessment_audience_role = relationship('AssessmentAudienceRole')

    def __repr__(self):
        return "<CDRole(id='%s', role_name='%s', role_abbreviation='%s', role_description='%s'," \
               "valid_from='%s', valid_to='%s')>" % (self.id, self.role_name,
                                                     self.role_abbreviation, self.role_description, self.valid_from,
                                                     self.valid_to)


class Stakeholder(Base):
    """
    This table contains the information about the stakeholders of the different cd_roles in the system
    """

    __tablename__ = 'stakeholder'

    abbreviation = Column(String(3), primary_key=True)
    stakeholder_name = Column(String(100), nullable=False)
    stakeholder_description = Column(String(250))
    valid_from = Column(ArrowType(timezone=True), default=arrow.utcnow())
    valid_to = Column(ArrowType(timezone=True))

    # One2Many relationship
    cd_role = relationship("CDRole")


class UserInRole(Base):
    """
    This table allows to store all related data from User who makes the executed_action
    """

    __tablename__ = 'user_in_role'

    # Generating the Sequence
    user_in_role_seq = Sequence('user_in_role_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=user_in_role_seq.next_value(), primary_key=True)
    valid_from = Column(ArrowType(timezone=True), default=arrow.utcnow())
    valid_to = Column(ArrowType(timezone=True))
    pilot_source_user_id = Column(String(20))

    # Many2One
    user_in_system_id = Column(Integer, ForeignKey('user_in_system.id'))
    cd_role_id = Column(Integer, ForeignKey('cd_role.id'))
    pilot_code = Column(String(4), ForeignKey('pilot.code'))

    # M2M relationships
    action = relationship("ExecutedAction", cascade="all, delete-orphan")
    frailty_status_timeline = relationship('FrailtyStatusTimeline',
                                           foreign_keys='FrailtyStatusTimeline.user_in_role_id')
    frailty_status_timeline_changed_by = relationship('FrailtyStatusTimeline',
                                                      foreign_keys='FrailtyStatusTimeline.changed_by')

    # One2Many relationship
    cr_profile = relationship("CRProfile", cascade="all, delete-orphan")
    variation_measure_value = relationship('VariationMeasureValue')
    numeric_indicator_value = relationship('NumericIndicatorValue')
    source_evidence = relationship('SourceEvidence')
    geriatric_factor_value = relationship('GeriatricFactorValue')
    assessment = relationship('Assessment')
    activity = relationship('Activity')

    # one2many (Multiple)
    created_by = relationship("CareProfile", foreign_keys='CareProfile.created_by')
    last_updated_by = relationship("CareProfile", foreign_keys='CareProfile.last_updated_by')

    def __repr__(self):
        return "<User(id='%s', valid_from='%s'. valid_to='%s')>" % (self.id, self.valid_from, self.valid_to)


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
        return "<UserInRole(username='%s', password='%s', created_date='%s')>" % (
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


class CRProfile(Base):
    """
    Initial referent personal and health profile data of the care recipient at the time of inclusion in observation.
    """

    __tablename__ = 'cr_profile'

    # Generating the Sequence
    cr_profile_seq = Sequence('cr_profile_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=cr_profile_seq.next_value(), primary_key=True)
    ref_height = Column(Float(4))
    ref_weight = Column(Float(4))
    ref_mean_blood_pressure = Column(Numeric(precision=5, scale=2))
    date = Column(ArrowType(timezone=True))
    birth_date = Column(ArrowType(timezone=True), nullable=False)
    gender = Column(Boolean, nullable=False)

    # Many2One
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'))

    def __repr__(self):
        return "<CRProfile(id='%s', ref_height='%s', ref_weight='%s', ref_mean_blood_pressure='%s', date='%s'," \
               "birth_date='%s', gender='%s')>" % (self.id, self.ref_height, self.ref_weight,
                                                   self.ref_mean_blood_pressure, self.date, self.birth_date,
                                                   self.gender)


class Pilot(Base):
    """
    The pilot table stores the information about the Pilots in a defined locations and what users are participating
    """

    __tablename__ = 'pilot'

    code = Column(String(4), unique=True, nullable=False, primary_key=True)
    pilot_name = Column(String(50), unique=True, nullable=False)
    population_size = Column(BigInteger)
    # One2Many
    user_in_role = relationship('UserInRole')
    location = relationship('Location')

    # M2M Relationship
    cd_pilot_detection_variable = relationship('CDPilotDetectionVariable')

    def __repr__(self):
        return "<Pilot(name='%s', pilot_code='%s', population_size='%s')>" % (self.name, self.code,
                                                                              self.population_size)


class Location(Base):
    """
    Users location in a specific time
    """
    __tablename__ = 'location'

    # Generating the Sequence
    location_id_seq = Sequence('location_id_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=location_id_seq.next_value(), primary_key=True)
    location_name = Column(String(50), unique=True, nullable=False)
    indoor = Column(Boolean)
    # One2Many
    pilot_code = Column(String(4), ForeignKey('pilot.code'), nullable=True)

    # many2many
    activity = relationship("LocationActivityRel")
    location_type = relationship("LocationLocationTypeRel")

    def __repr__(self):
        return "<Location(location_name='%s', indoor='%s')>" % (self.location_name, self.indoor)


class LocationType(Base):
    """
    Each location has a location type to have a logical order in the system
    """

    __tablename__ = 'location_type'

    # Generating the Sequence
    location_type_id_seq = Sequence('location_type_id_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=location_type_id_seq.next_value(), primary_key=True)
    location_type_name = Column(String(50), unique=True)


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


class Activity(Base):
    """
    Activity is a collection of different actions. For example "Make breakfast is an activity and could have some actions
    like:

        --> Put the milk in the bowl
        --> Open the fridge
        --> .....
    """
    __tablename__ = 'activity'

    # Generating the Sequence
    activity_id_seq = Sequence('activity_id_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=activity_id_seq.next_value(), primary_key=True)
    activity_name = Column(String(50))
    activity_description = Column(String(200))
    creation_date = Column(ArrowType(timezone=True), default=arrow.utcnow())
    instrumental = Column(Boolean, default=False, nullable=False)
    data_source_type = Column(String(200))

    # TODO for the moment this two field will be nullable, in order to insert new activities.
    # FK
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'), nullable=True)
    time_interval_id = Column(Integer, ForeignKey('time_interval.id'), nullable=True)

    # One2one
    eam = relationship("EAM", uselist=False, back_populates="activity")

    # one2many
    expected_inter_behaviour = relationship("InterActivityBehaviourVariation",
                                            foreign_keys='InterActivityBehaviourVariation.expected_activity_id')
    real_inter_behaviour = relationship("InterActivityBehaviourVariation",
                                        foreign_keys='InterActivityBehaviourVariation.real_activity_id')

    variation_measure_value = relationship('VariationMeasureValue')

    def __repr__(self):
        return "<Activity(activity_name='%s')>" % self.activity_name


class CDAction(Base):
    """
    Action registration
    """
    __tablename__ = 'cd_action'

    # Generating the Sequence
    cd_action_id_seq = Sequence('cd_action_id_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=cd_action_id_seq.next_value(), primary_key=True)
    action_name = Column(String(50), unique=True)
    action_description = Column(String(250))

    # one2many
    eam = relationship("EAM")  # TODO this should be deleted

    def __repr__(self):
        return "<CDAction(action_name='%s', category='%s')>" % (
            self.action_name, self.category)


# TODO consider to remove this class from this table design

class EAM(Base):  # DECIDE
    """
    This table stores the duration of each related action/activity in a simple place.
    """

    __tablename__ = 'eam'

    # Generating the Sequence
    eam_seq = Sequence('eam_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=eam_seq.next_value(), primary_key=True)
    duration = Column(Integer)
    # one2one
    activity_id = Column(Integer, ForeignKey('activity.id'))
    activity = relationship("Activity", back_populates="eam")
    # one2many
    cd_action_id = Column(Integer, ForeignKey('cd_action.id'))

    # TODO change this to poin
    # many2many
    # start_range = relationship("EAMStartRangeRel")
    # simple_location = relationship("EAMSimpleLocationRel")

    def __repr__(self):
        return "<EAM(duration='%s')>" % self.duration


class TimeInterval(Base):
    """
    Defines some different interval times to calculate the variation measures over an action.
    """

    __tablename__ = 'time_interval'

    # Generating the Sequence
    time_interval_seq = Sequence('time_interval_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=time_interval_seq.next_value(), primary_key=True)
    interval_start = Column(ArrowType(timezone=True), nullable=False)
    interval_end = Column(ArrowType(timezone=True), nullable=False)  # Calculated by the period

    # Many2One
    typical_period = Column(String(3), ForeignKey('cd_typical_period.typical_period'))

    # Relationships
    variation_measure_value = relationship('VariationMeasureValue')
    numeric_indicator_value = relationship('NumericIndicatorValue')
    geriatric_factor_value = relationship('GeriatricFactorValue')
    activity = relationship('Activity')

    def __repr__(self):
        return "<TimeInterval(interval_start='%s', interval_end='%s')>" % \
               (self.interval_start,
                self.interval_end)


class CDTypicalPeriod(Base):
    """
    Duration of the typical period, if fixed. Should be interval data type.
    """

    __tablename__ = 'cd_typical_period'

    typical_period = Column(String(3), primary_key=True)
    period_description = Column(String(50), nullable=False)
    typical_duration = Column(ArrowType(timezone=True))

    # One2Many
    time_interval = relationship('TimeInterval')
    cd_detection_variable = relationship('CDDetectionVariable')

    def __repr__(self):
        return "<CDTypicalPeriod(typical_period='%s', typical_duration='%s')>" % \
               (self.typical_period,
                self.typical_duration)


class VariationMeasureValue(Base):
    """
    Stores different variation measures values over the time.
    """

    __tablename__ = 'variation_measure_value'

    # Generating the Sequence
    variation_measure_value_seq = Sequence('variation_measure_value_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=variation_measure_value_seq.next_value(), primary_key=True)
    measure_value = Column(Numeric(precision=30, scale=10), nullable=False)

    data_source_type = Column(String(1000))
    extra_information = Column(String(1000))

    # Many2One
    activity_id = Column(Integer, ForeignKey('activity.id'))
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'), nullable=False)
    measure_type_id = Column(Integer, ForeignKey('cd_detection_variable.id'), nullable=False)
    time_interval_id = Column(Integer, ForeignKey('time_interval.id'), nullable=False)

    def __repr__(self):
        return "<VariationMeasureValue(id='%s', detection_variable_name='%s')>" % \
               (self.id, self.measure_value)


class NumericIndicatorValue(Base):
    """
    Entity intended to store the values of Numeric Indicators (NUI), for time intervals.
    The type of the value record is determined from the DetectionVariable entity, which also has a reflexive
    one-to-many relation denoting which NUIs aggregate to which Sub-Factor, which Sub-Factors constitute which Factor,
    Factors a GEF Group etc.
    """

    __tablename__ = 'numeric_indicator_value'

    # Generating the Sequence
    numeric_indicator_value_seq = Sequence('numeric_indicator_value_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=numeric_indicator_value_seq.next_value(), primary_key=True)
    nui_value = Column(Numeric(precision=10, scale=2), nullable=False)
    data_source_type = Column(String(1000))

    # Many 2 one tables
    nui_type_id = Column(Integer, ForeignKey('cd_detection_variable.id'))
    time_interval_id = Column(Integer, ForeignKey('time_interval.id'), nullable=False)
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'))

    def __repr__(self):
        return "<NumericIndicatorValue(id='%s', nui_value='%s')>" % \
               (self.id, self.nui_value)


# TODO identify the purpose of this table.
class CDDataSourceType(Base):
    """
    Give some information about what is the data source, and its descriptions
    """

    __tablename__ = 'cd_data_source_type'

    data_source_type = Column(String(3), primary_key=True)
    data_source_type_description = Column(String(250), nullable=False)
    obtrusive = Column(Boolean)

    def __repr__(self):
        return "<CDDataSourceType(data_source_type='%s', data_source_type_description='%s', obtrusive='%s')>" % \
               (self.data_source_type, self.data_source_type_description,
                self.obtrusive)


class SourceEvidence(Base):
    """
    Saves data from geriatric to show evidences using texts and images uploaded to the API
    """

    __tablename__ = 'source_evidence'

    geriatric_factor_id = Column(Integer, ForeignKey('geriatric_factor_value.id'), primary_key=True)
    text_evidence = Column(Text)
    multimedia_evidence = Column(LargeBinary)
    uploaded = Column(ArrowType(timezone=True), default=arrow.utcnow(), nullable=False)

    # Many2One
    author_id = Column(Integer, ForeignKey('user_in_role.id'))

    def __repr__(self):
        return "<SourceEvidence(geriatric_factor_id='%s', text_evidence='%s', uploaded='%s', author_id='%s')>" % \
               (self.geriatric_factor_id, self.text_evidence, self.uploaded, self.author_id)


class GeriatricFactorValue(Base):
    """
    Hierarchic entity intended to store the values of Geriatric Factors (GEF), Sub-Factors(GES), and GEF groups
    (Behavioural, Contextual, Overall).The type of the value record is determined from the DetectionVariable entity,
    which also has a reflexive one-to-many relation denoting which NUIs aggregate to which Sub-Factor, which
    Sub-Factors constitute which Factor, Factors a GEF Group etc.
    """

    __tablename__ = 'geriatric_factor_value'

    # Generating the Sequence
    geriatric_factor_value_seq = Sequence('geriatric_factor_value_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=geriatric_factor_value_seq.next_value(), primary_key=True)
    gef_value = Column(Numeric(precision=3, scale=2), nullable=False)
    derivation_weight = Column(Numeric(precision=5, scale=2))
    data_source_type = Column(String(1000))
    # Many2One relationships
    time_interval_id = Column(Integer, ForeignKey('time_interval.id'), nullable=False)
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'), nullable=False)
    gef_type_id = Column(Integer, ForeignKey('cd_detection_variable.id'))

    # M2M
    assessed_gef_value_set = relationship('AssessedGefValueSet')

    def __repr__(self):
        return "<GeriatricFactorValue(id='%s', gef_value='%s', derivation_weight='%s')>" % \
               (self.id, self.gef_value,
                self.derivation_weight)


class Assessment(Base):
    """
    Assessments are input by geriatric/medical/caregiver staff (author_id) on specific geriatric factor or detection
    variable values (GES,GEF,GFG) represented as data points on interactive dashboards. An assessment can consist of a
    comment and flag markers (for risk status or data validity), any of the 3.
    """

    __tablename__ = 'assessment'

    # Generating the Sequence
    assessment_seq = Sequence('assessment_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=assessment_seq.next_value(), primary_key=True)
    assessment_comment = Column(String)
    data_validity_status = Column(String(1))
    created = Column(ArrowType(timezone=True), default=arrow.utcnow(), nullable=False)
    updated = Column(ArrowType(timezone=True))

    # Many2One
    risk_status = Column(String(1), ForeignKey('cd_risk_status.risk_status'), nullable=False)
    author_id = Column(Integer, ForeignKey('user_in_role.id'))

    def __repr__(self):
        return "<Assessment(assessment_comment='%s', data_validity_status='%s')>" % (self.activity_name,
                                                                                     self.data_validity_status)


class CareProfile(Base):
    """
    Care profile stores individuals related data about interventions, attentions and the summary
    of their personal information.
    """

    __tablename__ = 'care_profile'

    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'), primary_key=True)
    individual_summary = Column(String, nullable=False)
    attention_status = Column(String(1))
    intervention_status = Column(String(1))
    last_intervention_date = Column(ArrowType(timezone=True))
    created = Column(ArrowType(timezone=True), default=arrow.utcnow(), nullable=False)
    last_updated = Column(ArrowType(timezone=True))
    # Many 2 one Relationships
    created_by = Column(Integer, ForeignKey('user_in_role.id'), nullable=False)
    last_updated_by = Column(Integer, ForeignKey('user_in_role.id'))

    def __repr__(self):
        return "<CareProfile(user_in_role_id='%s', individual_summary='%s', attention_status='%s', " \
               "intervention_status = '%s', last_intervention_date='%s')>" % \
               (self.user_in_role_id, self.individual_summary, self.attention_status,
                self.intervention_status, self.last_intervention_date)


class CDFrailtyStatus(Base):
    """
    Contains the information about the frailty status and its description
    """

    __tablename__ = 'cd_frailty_status'

    frailty_status = Column(String(9), primary_key=True)
    frailty_status_description = Column(String(255))

    # This is connected through M2M relationship

    def __repr__(self):
        return "<CDFrailtyStatus(frailty_status='%s', frailty_status_description='%s')>" % \
               (self.frailty_status,
                self.frailty_status_description)


class CDRiskStatus(Base):
    """
    Classification of risk statuses, initially "W" (risk Warning, moderate or suspect risk), and "A"
    (risk Alert, evident risk). Null is presumed low or no risk (when this status is foreign key).
    """

    __tablename__ = 'cd_risk_status'

    risk_status = Column(String(1), primary_key=True)
    risk_status_description = Column(String(250), nullable=False)
    confidence_rating = Column(Numeric(precision=3, scale=2), nullable=False)
    icon_image = Column(LargeBinary)

    # One2Many
    assessment = relationship('Assessment')

    def __repr__(self):
        return "<CDRiskStatus(risk_status='%s', risk_status_description='%s', confidence_rating='%s')>" % \
               (self.risk_status, self.risk_status_description,
                self.confidence_rating)


class CDDetectionVariable(Base):
    """
    Stores the definitions and descriptions of detection variables defined on all levels - Measures, NUIs, GEFs, GESs,
    and Factor Groups (including "Overall" as specific parent factor group). DetectionVariable entity that is related 
    through foreign keys to VariationMeasure, NumericIndicator, and Geriatric Factor entities. It can be determined
    through the value of DetectionVariableType attribute (MEA, NUI, GES, GEF...) to which table exactly is the each
    record in DetectionVariable related. The entity has a reflexive one-to-many relation defining the hierarchy of the
    variables - denoting which NUIs aggregate to which Sub-Factor, which Sub-Factors constitute which Factor, Factors a
    GEF Group etc.
    """

    __tablename__ = 'cd_detection_variable'

    # Generating the Sequence
    cd_detection_variable_seq = Sequence('cd_detection_variable_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=cd_detection_variable_seq.next_value(), primary_key=True)
    detection_variable_name = Column(String(100), nullable=False)
    valid_from = Column(ArrowType(timezone=True), default=arrow.utcnow())
    valid_to = Column(ArrowType(timezone=True))
    default_derivation_weight = Column(Numeric(precision=5, scale=2))
    source_datatype = Column(String(25))
    base_unit = Column(String(50))

    # FK
    detection_variable_type = Column(String(3), ForeignKey('cd_detection_variable_type.detection_variable_type'),
                                     nullable=False)
    default_typical_period = Column(String(3), ForeignKey('cd_typical_period.typical_period'))

    # Self FK column
    cd_detection_variable = relationship('CDDetectionVariable', remote_side=[id])  # Self relationship with id column
    derived_detection_variable_id = Column(Integer, ForeignKey('cd_detection_variable.id'))

    # Relationship
    variation_measure_value = relationship('VariationMeasureValue')
    numeric_indicator_value = relationship('NumericIndicatorValue')
    geriatric_factor_value = relationship('GeriatricFactorValue')

    def __repr__(self):
        return "<CDDetectionVariable(id='%s', detection_variable_name='%s', derivation_weight='%s')>" % \
               (self.id, self.detection_variable_name, self.derivation_weight)


class CDDetectionVariableType(Base):
    """
    Classification of types of defined detection variables (MEA, NUI, GES, GEF...
    """

    __tablename__ = 'cd_detection_variable_type'

    detection_variable_type = Column(String(3), primary_key=True)
    detection_variable_type_description = Column(String(255), nullable=False)

    # Relationships
    cd_detection_variable = relationship('CDDetectionVariable')

    def __repr__(self):
        return "<CDDetectionVariableType(detection_variable_type='%s', detection_variable_type_description='%s')>" % \
               (self.detection_variable_type,
                self.detection_variable_type_description)


# TODO ask to change the name of this table to InterBehaviour or delete it
# In AR database this class is called InterBehaviour
class InterActivityBehaviourVariation(Base):
    """
    Contains the variations of the behaviours in the intra activity.
    """

    __tablename__ = 'inter_activity_behaviour_variation'

    # Generating the Sequence
    inter_activity_behaviour_variation_seq = Sequence('inter_activity_behaviour_variation_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=inter_activity_behaviour_variation_seq.next_value(), primary_key=True)
    deviation = Column(Float(10))
    # many2one relationships
    expected_activity_id = Column(Integer, ForeignKey('activity.id'))
    real_activity_id = Column(Integer, ForeignKey('activity.id'))
    numeric_indicator_id = Column(Integer, ForeignKey('numeric_indicator_value.id'))

    def __repr__(self):
        return "<InterActivityBehaviourVariation(id='%s', deviation='%s')>" % \
               (self.id, self.deviation)


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


class Metric(Base):
    """
    Some actions has a random valued metrics. This metrics are an extra information that can be used for different
    purposes. This table record each different metric in the sytem.

    """

    __tablename__ = 'metric'

    # Generating the Sequence
    metric_seq = Sequence('metric_seq', metadata=Base.metadata)
    # Creating the columns
    id = Column(Integer, server_default=metric_seq.next_value(), primary_key=True)
    name = Column(String(50))
    description = Column(String(255), nullable=True)
    # M2M relationship
    cd_action_metric = relationship('CDActionMetric')
