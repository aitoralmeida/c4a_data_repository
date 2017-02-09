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
from sqlalchemy import Column, Integer, String, Boolean, Sequence, Float, BigInteger, ForeignKey, LargeBinary, \
    TIMESTAMP, Text, TypeDecorator, event, MetaData
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


class FrailtyStatusTimeline(Base):                                                          # OK
    """
    Multiple relationship intermediate table

    user_in_role -- time_interval -- cd_frailty_status
    """

    __tablename__ = 'frailty_status_timeline'

    changed = Column(TIMESTAMP, primary_key=True)
    user_in_role_id = Column(Integer, primary_key=True)     # TODO ensure that this class is OK

    # user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'), primary_key=True)
    time_interval_id = Column(Integer, ForeignKey('time_interval.id'), primary_key=True)
    changed_by = Column(Integer, ForeignKey('user_in_role.id'))
    frailty_notice = Column(String(200))

    # Many2One
    frailty_status = Column(String(9), ForeignKey('cd_frailty_status.frailty_status'), nullable=False)

    # Relationships
    time_interval = relationship('TimeInterval')
    cd_frailty_status = relationship('CDFrailtyStatus')


class CDPilotDetectionVariable(Base):                                                       # OK
    """
    Pilot < -- > CDDetectionVariable
    """

    __tablename__ = 'cd_pilot_detection_variable'

    pilot_id = Column(Integer, ForeignKey('pilot.id'), primary_key=True) # TODO name or ID?
    detection_variable_id = Column(Integer, ForeignKey('cd_detection_variable.id'), primary_key=True)

    # Relationship with other Tables
    cd_detection_variable = relationship('CDDetectionVariable')


class AssessedGefValueSet(Base):                                                            # OK
    """
    GeriatricFactorValue < -- > Assessment
    """

    __tablename__ = 'assessed_gef_value_set'

    gef_value_id = Column(Integer, ForeignKey('geriatric_factor_value.id'), primary_key=True)
    assessment_id = Column(Integer, ForeignKey('assessment.id'), ForeignKey('assessment.id'), primary_key=True)

    # Relationship with other Tables
    assessment = relationship('Assessment')


class AssessmentAudienceRole(Base):                                                         # OK
    """
    cd_role <--> assessment
    """

    __tablename__ = 'assessment_audience_role'

    assessment_id = Column(Integer, ForeignKey('assessment.id'), primary_key=True)
    role_id = Column(Integer, ForeignKey('cd_role.id'), primary_key=True)
    assigned = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    # Relationship with other Tables
    cd_role = relationship('Assessment')


class ExecutedAction(Base):                                                                 # OK
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
    payload = Column(String(50))
    extra_information = Column(Text)
    # Relationship with other TABLES
    action = relationship("Action")
    activity = relationship("Activity")
    location = relationship("Location")


"""
Base tables. Here is defined the basic tables.
"""


class CDRole(Base):                                                                         # OK
    """
    This table contains information about the roles of the system. It stores the role information and its
    validity in the system
    """

    __tablename__ = 'cd_role'

    id = Column(Integer, Sequence('cd_role_seq'), primary_key=True)
    role_name = Column(String(50), nullable=False)
    role_abbreviation = Column(String(3))
    role_description = Column(String(200), nullable=False)
    valid_from = Column(TIMESTAMP, nullable=False)
    valid_to = Column(TIMESTAMP)

    # One2Many
    user_in_role = relationship('UserInRole')

    # M2M Relationship
    assessment_audience_role = relationship('AssessmentAudienceRole')

    def __repr__(self):
        return "<CDRole(id='%s', role_name='%s', role_abbreviation='%s', role_description='%s'," \
               "valid_from='%s', valid_to='%s')>" % (self.id, self.role_name,
                                                     self.role_abbreviation, self.role_description, self.valid_from,
                                                     self.valid_to)


class UserInRole(Base):                                                                         # OK
    """
    This table allows to store all related data from User who makes the executed_action
    """

    __tablename__ = 'user_in_role'

    id = Column(String(75), primary_key=True)
    valid_from = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    valid_to = Column(TIMESTAMP)

    # Many2One
    user_registered_id = Column(Integer, ForeignKey('user_registered.id'))
    cd_role_id = Column(Integer, ForeignKey('cd_role.id'))
    pilot_id = Column(String(50), ForeignKey('pilot.id')) #             TODO ID OR NAME?

    # M2M relationships
    action = relationship("ExecutedAction", cascade="all, delete-orphan")
    frailty_status_timeline = relationship('FrailtyStatusTimeline')

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


# TODO This table seems to be deleted due to AR_DATABASE has the access protocol. Ensure that we need.
class UserRegistered(Base):                                                                     # OK
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
    # historical = relationship('Historical')
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


class CRProfile(Base):                                                                              # OK
    """
    Initial referent personal and health profile data of the care recipient at the time of inclusion in observation.
    """

    __tablename__ = 'cr_profile'

    id = Column(Integer, Sequence('cr_profile_seq'), primary_key=True)
    ref_height = Column(Float(4))
    ref_weight = Column(Float(4))
    ref_mean_blood_pressure = Column(Float(5))         # TODO research how to solve precission
    date = Column(TIMESTAMP)
    birth_date = Column(TIMESTAMP)
    gender = Column(Boolean)

    # Many2One
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'))

    def __repr__(self):
        return "<CRProfile(id='%s', ref_height='%s', ref_weight='%s', ref_mean_blood_pressure='%s', date='%s'," \
               "birth_date='%s', gender='%s')>" % (self.id, self.ref_height, self.ref_weight,
                                                   self.ref_mean_blood_pressure, self.date, self.birth_date,
                                                   self.gender)


class Pilot(Base):                                                                                  # OK
    """
    The pilot table stores the information about the Pilots in a defined locations and what users are participating
    """

    __tablename__ = 'pilot'

    id = Column(Integer, primary_key=True)  # TODO ask if this table can use name as PK?
    name = Column(String(50))
    pilot_code = Column(String(4), unique=True, nullable=False)
    population_size = Column(BigInteger)
    # One2Many
    user_in_role = relationship('UserInRole')
    location = relationship('Location')

    # M2M Relationship
    cd_pilot_detection_variable = relationship('CDPilotDetectionVariable')

    def __repr__(self):
        return "<Pilot(name='%s', pilot_code='%s', population_size='%s')>" % (self.name, self.pilot_code,
                                                                              self.population_size)


# TODO considerar to add a M2M relationship with Activity to fullfull the requierements of AR
class Location(Base):                                                                               # OK
    """
    Users location in a specific time
    """
    __tablename__ = 'location'

    id = Column(Integer, Sequence('location_id_seq'), primary_key=True)
    location_name = Column(String(75))
    indoor = Column(Boolean)
    # One2Many
    pilot_id = Column(String(50), ForeignKey('pilot.id'), nullable=True)  # TODO name or id?

    # many2many
    # activity = relationship("LocationActivityRel") # TODO ask for intermediate TABLE multiple locations

    def __repr__(self):
        return "<Location(location_name='%s', indoor='%s')>" % (self.location_name, self.indoor)


class Activity(Base):                                                                               # OK
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

    # FK
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'), nullable=False)
    time_interval_id = Column(Integer, ForeignKey('time_interval.id'), nullable=False)
    data_source_type = Column(String(3), ForeignKey('cd_data_source_type.data_source_type'))

    # One2one
    eam = relationship("EAM", uselist=False, back_populates="activity")

    # one2many
    expected_inter_behaviour = relationship("InterActivityBehaviourVariation",
                                            foreign_keys='InterActivityBehaviourVariation.expected_activity_id')
    real_inter_behaviour = relationship("InterActivityBehaviourVariation",
                                        foreign_keys='InterActivityBehaviourVariation.real_activity_id')

    variation_measure_value = relationship('VariationMeasureValue')



    def __repr__(self):
        return "<Activity(activity_name='%s', activity_start_date='%s', activity_end_date='%s', creation_date='%s')>"  \
               % (self.activity_name, self.activity_start_date, self.activity_end_date, self.creation_date)


class Action(Base):                                                                                   # OK
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


class EAM(Base):                                                                                      # DECIDE
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

    # TODO this is not listed in this DATABASE, Ensure to add here.
    # many2many
    #start_range = relationship("EAMStartRangeRel")
    #simple_location = relationship("EAMSimpleLocationRel")

    def __repr__(self):
        return "<EAM(duration='%s')>" % self.duration


class TimeInterval(Base):                                                                   # Ok
    """
    Defines some different interval times to calculate the variation measures over an action.
    """

    __tablename__ = 'time_interval'

    id = Column(Integer, Sequence('time_interval_seq'), primary_key=True)
    interval_start = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    interval_end = Column(TIMESTAMP)

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


class CDTypicalPeriod(Base):                                                                    # OK
    """
    Duration of the typical period, if fixed. Should be interval data type.
    """

    __tablename__ = 'cd_typical_period'

    typical_period = Column(String(3), primary_key=True)
    period_description = Column(String(50), nullable=False)
    typical_duration = Column(TIMESTAMP)

    # One2Many
    time_interval = relationship('TimeInterval')

    def __repr__(self):
        return "<CDTypicalPeriod(typical_period='%s', typical_duration='%s')>" % \
               (self.typical_period,
                self.typical_duration)


class VariationMeasureValue(Base):                                                          # oK
    """
    Stores different varion measures values over the time.
    """

    __tablename__ = 'variation_measure_value'

    id = Column(Integer, Sequence('variation_measure_value_seq'), primary_key=True)
    measure_value = Column(Float(4))
    # Many2One
    activity_id = Column(Integer, ForeignKey('activity.id'))
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'), nullable=False)
    measure_type_id = Column(Integer, ForeignKey('cd_detection_variable.id'), nullable=False)
    time_interval_id = Column(Integer, ForeignKey('time_interval.id'), nullable=False)
    data_source_type = Column(String(3), ForeignKey('cd_data_source_type.data_source_type'))

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

    id = Column(Integer, Sequence('numeric_indicator_value_seq'), primary_key=True)
    nui_value = Column(Float(10), nullable=False)          # TODO research how to solve precission

    # Many 2 one tables
    nui_type_id = Column(Integer, ForeignKey('cd_detection_variable.id'))
    time_interval_id = Column(Integer, ForeignKey('time_interval.id'))
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'))
    data_source_type = Column(String(3), ForeignKey('cd_data_source_type.data_source_type'))

    def __repr__(self):
        return "<NumericIndicatorValue(id='%s', nui_value='%s')>" % \
               (self.id, self.nui_value)


class CDDataSourceType(Base):
    """
    Give some information about what is the data source, and its descriptions
    """

    __tablename__ = 'cd_data_source_type'

    data_source_type = Column(String(3), primary_key=True)
    data_source_type_description = Column(String(250), nullable=False)
    obtrusive = Column(Boolean)

    # Relationship
    variation_measure_value = relationship('VariationMeasureValue')
    numeric_indicator_value = relationship('NumericIndicatorValue')
    geriatric_factor_value = relationship('GeriatricFactorValue')
    activity = relationship('Activity')

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
    uploaded = Column(TIMESTAMP, default=datetime.datetime.utcnow)

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

    id = Column(Integer, Sequence('geriatric_factor_value_seq'), primary_key=True)
    gef_value = Column(Float(3), nullable=False)           # TODO research how to solve precission
    derivation_weight = Column(Float(5))           # TODO research how to solve precission

    # Many2One relationships
    time_interval_id = Column(Integer, ForeignKey('time_interval.id'), nullable=False)
    user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'), nullable=False)
    data_source_type = Column(String(3), ForeignKey('cd_data_source_type.data_source_type'))
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

    id = Column(Integer, Sequence('assessment_seq'), primary_key=True)
    assessment_comment = Column(String)
    data_validity_status = Column(String(1))
    created = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated = Column(TIMESTAMP)

    # Many2One
    risk_status = Column(String(1), ForeignKey('cd_risk_status.risk_status'))
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
    individual_summary = Column(String)
    attention_status = Column(String(1))
    intervention_status = Column(String(1))
    last_intervention_date = Column(TIMESTAMP)
    created = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    last_updated = Column(TIMESTAMP)

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
    confidence_rating = Column(Float(3), nullable=False)           # TODO research how to solve precission
    icon_image = Column(LargeBinary)

    # One2Many
    assessment = relationship('Assessment')

    def __repr__(self):
        return "<CDRiskStatus(risk_status='%s', risk_status_description='%s', confidence_rating='%s')>" % \
               (self.risk_status, self.risk_status_description,
                self.confidence_rating)


class CDDetectionVariable(Base):                                                                # OK
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

    id = Column(Integer, Sequence('numeric_indicator_value_seq'), primary_key=True)
    detection_variable_name = Column(String(100), nullable=False)
    valid_from = Column(TIMESTAMP, default=datetime.datetime.utcnow())
    valid_to = Column(TIMESTAMP)
    derivation_weight = Column(Float(5))               # TODO research how to solve precission

    # FK
    detection_variable_type = Column(String(3), ForeignKey('cd_detection_variable_type.detection_variable_type'),
                                     nullable=False)
    # Self FK column
    cd_detection_variable = relationship('CDDetectionVariable', remote_side=[id])   # Self relationship with id column
    derived_detection_variable_id = Column(Integer, ForeignKey('cd_detection_variable.id'))

    # Relationship
    variation_measure_value = relationship('VariationMeasureValue')
    numeric_indicator_value = relationship('NumericIndicatorValue')
    geriatric_factor_value = relationship('GeriatricFactorValue')

    def __repr__(self):
        return "<CDDetectionVariable(id='%s', detection_variable_name='%s', derivation_weight='%s')>" % \
               (self.id, self.detection_variable_name, self.derivation_weight)


class CDDetectionVariableType(Base):                                                            # OK
    """
    Classification of types of defined detection variables (MEA, NUI, GES, GEF...
    """

    __tablename__ = 'cd_detection_variable_type'

    detection_variable_type = Column(String(3), primary_key=True)
    detection_variable_type_description = Column(String(50), nullable=False)

    # Relationships
    cd_detection_variable = relationship('CDDetectionVariable')

    def __repr__(self):
        return "<CDDetectionVariableType(detection_variable_type='%s', detection_variable_type_description='%s')>" % \
               (self.detection_variable_type,
                self.detection_variable_type_description)


# In AR database this class is called InterBehaviour
class InterActivityBehaviourVariation(Base):
    """
    Contains the variations of the behaviours in the intra activity.
    """

    __tablename__ = 'inter_activity_behaviour_variation'

    id = Column(Integer, Sequence('inter_activity_behaviour_variation_seq'), primary_key=True)
    deviation = Column(Float)

    # many2one relationships
    expected_activity_id = Column(Integer, ForeignKey('activity.id'))
    real_activity_id = Column(Integer, ForeignKey('activity.id'))
    numeric_indicator_id = Column(Integer, ForeignKey('numeric_indicator_value.id'))

    def __repr__(self):
        return "<InterActivityBehaviourVariation(id='%s', deviation='%s')>" % \
               (self.id, self.deviation)
