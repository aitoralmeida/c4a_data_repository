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
from sqlalchemy import Column, Integer, String, Boolean, Sequence, Float, BigInteger, ForeignKey, LargeBinary,\
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


####### DEFINITION OF ALL NEEDED TABLES

# TODO I need to use this tables or I can refer directly to ar_schema?

############################################################################################################
############################################################################################################
############################################################################################################

# Base tables
class CDRole(Base):
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

    def __repr__(self):
        return "<CDRole(id='%s', role_name='%s', role_abbreviation='%s', role_description='%s'," \
               "valid_from='%s', valid_to='%s')>" % (self.id, self.role_name,
                                                     self.role_abbreviation, self.role_description, self.valid_from,
                                                     self.valid_to)


class UserInRole(Base):
    """
    This table allows to store all related data from User who makes the executed_action
    """

    __tablename__ = 'user_in_role'

    id = Column(String(75), primary_key=True)
    valid_from = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    valid_to = Column(TIMESTAMP)
    # m2m
    action = relationship("ExecutedAction", cascade="all, delete-orphan")
    # one2many
    # stake_holder_name = Column(String(25), ForeignKey('stake_holder.name'))
    user_authenticated_id = Column(Integer, ForeignKey('user_authenticated.id'))
    cd_role_id = Column(Integer, ForeignKey('cd_role.id'))
    pilot_name = Column(String(50), ForeignKey('pilot.name'))

    def __repr__(self):
        return "<User(id='%s', valid_from='%s'. valid_to='%s')>" % (self.id, self.valid_from, self.valid_to)


class UserAuthenticated(Base):
    """
    Base data of the users
    """
    __tablename__ = 'user_authenticated'

    id = Column(Integer, Sequence('user_authenticated_seq'), primary_key=True)
    username = Column(Text, nullable=False, unique=True)
    password = Column(Password(rounds=13), nullable=False)
    # Or specify a cost factor other than the default 13
    # password = Column(Password(rounds=10))
    # Without rounds System will use 13 rounds by default
    created_date = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    # one2many
    historical = relationship('Historical')
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

############################################################################################################
############################################################################################################
############################################################################################################
############################################################################################################


# TODO @@@@@





# Vladimir's base TABLES
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

    # Many 2 One relationships

    def __repr__(self):
        return "<Assessment(assessment_comment='%s', data_validity_status='%s')>" % (self.activity_name,
                                                                                     self.data_validity_status)


class CDRiskStatus(Base):
    """
    Classification of risk statuses, initially "W" (risk Warning, moderate or suspect risk), and "A"
    (risk Alert, evident risk). Null is presumed low or no risk (when this status is foreign key).
    """

    __tablename__ = 'cd_risk_status'

    risk_status = Column(String(1), primary_key=True)
    risk_status_description = Column(String(250), nullable=False)
    confidence_rating = Column(Float(3, precision=2), nullable=False)
    icon_image = Column(LargeBinary)

    def __repr__(self):
        return "<CDRiskStatus(risk_status='%s', risk_status_description='%s', confidence_rating='%s')>" % \
                                                    (self.risk_status, self.risk_status_description,
                                                     self.confidence_rating)


class GeriatricFactorValue(Base):
    """
    Hierarchic entity intended to store the values of Geriatric Factors (GEF), Sub-Factors(GES), and GEF groups
    (Behavioural, Contextual, Overall).The type of the value record is determined from the DetectionVariable entity,
    which also has a reflexive one-to-many relation denoting which NUIs aggregate to which Sub-Factor, which
    Sub-Factors constitute which Factor, Factors a GEF Group etc.
    """

    __tablename__ = 'geriatric_factor_value'

    id = Column(Integer, Sequence('geriatric_factor_value_seq'), primary_key=True)
    gef_value = Column(Float(3, precision=2), nullable=False)
    derivation_weight = Column(Float(5, precision=2))

    # One 2 Many relationships

    def __repr__(self):
        return "<GeriatricFactorValue(id='%s', gef_value='%s', derivation_weight='%s')>" % \
                                                    (self.id, self.gef_value,
                                                     self.derivation_weight)


class NumericIndicatorValue(Base):
    """
    Entity intended to store the values of Numeric Indicators (NUI), for time intervals.
    The type of the value record is determined from the DetectionVariable entity, which also has a reflexive
    one-to-many relation denoting which NUIs aggregate to which Sub-Factor, which Sub-Factors constitute which Factor,
    Factors a GEF Group etc.
    """

    __tablename__ = 'numeric_indicator_value'

    id = Column(Integer, Sequence('numeric_indicator_value_seq'), primary_key=True)
    nui_value = Column(Float(10, precision=2), nullable=False)

    # One 2 Many tables

    def __repr__(self):
        return "<NumericIndicatorValue(id='%s', nui_value='%s')>" % \
                                                    (self.id, self.nui_value)


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

    id = Column(Integer, Sequence('numeric_indicator_value_seq'), primary_key=True)
    detection_variable_name = Column(String(100))
    valid_from = Column(TIMESTAMP)
    valid_to = Column(TIMESTAMP)
    derivation_weight = Column(Float(5, precision=2))

    # One 2 Many relationships

    def __repr__(self):
        return "<CDDetectionVariable(id='%s', detection_variable_name='%s', derivation_weight='%s')>" % \
                                                    (self.id, self.detection_variable_name, self.derivation_weight)


class VariationMeasureValue(Base):
    """
    Stores different varion measures values over the time.
    """

    __tablename__ = 'variation_measure_value'

    id = Column(Integer, Sequence('variation_measure_value_seq'), primary_key=True)
    measure_value = Column(Float(4))

    # One 2 Many

    def __repr__(self):
        return "<VariationMeasureValue(id='%s', detection_variable_name='%s')>" % \
                                                    (self.id, self.measure_value)


class InterActivityBehaviourVariation(Base):
    """
    Contains the variations of the behaviours in the intra activity.
    """

    id = Column(Integer, Sequence('inter_activity_behaviour_variation_seq'), primary_key=True)
    deviation = Column(Float)

    # One to many


    def __repr__(self):
        return "<InterActivityBehaviourVariation(id='%s', deviation='%s')>" % \
                                                    (self.id, self.deviation)


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


class CRProfile(Base):
    """
    Initial referent personal and health profile data of the care recipient at the time of inclusion in observation.
    """

    __tablename__ = 'cr_profile'

    id = Column(Integer, Sequence('cr_profile_seq'), primary_key=True)
    ref_height = Column(Float(4))
    ref_weight = Column(Float(4))
    ref_mean_blood_pressure = Column(Float(5, precision=2))
    date = Column(TIMESTAMP)
    birth_date = Column(TIMESTAMP)
    gender = Column(Boolean)

    # One to many

    def __repr__(self):
        return "<CRProfile(id='%s', ref_height='%s', ref_weight='%s', ref_mean_blood_pressure='%s', date='%s'," \
               "birth_date='%s', gender='%s')>" % (self.id, self.ref_height, self.ref_weight,
                                                   self.ref_mean_blood_pressure, self.date, self.birth_date,
                                                   self.gender)


class CDDetectionVariableType(Base):
    """
    Classification of types of defined detection variables (MEA, NUI, GES, GEF...
    """

    __tablename__ = 'cd_detection_variable_type'

    detection_variable_type = Column(String(3), primary_key=True)
    detection_variable_type_description = Column(String(50), nullable=False)

    # One 2 many relationships

    def __repr__(self):
        return "<CDDetectionVariableType(detection_variable_type='%s', detection_variable_type_description='%s')>" % \
                                                    (self.detection_variable_type,
                                                     self.detection_variable_type_description)


class CDFrailtyStatus(Base):
    """
    Contains the frailty status amd information for each frailti status timeline entry
    """

    __tablename__ = 'cd_frailty_status'

    frailty_status = Column(String(9), primary_key=True)
    frailty_status_description = Column(String(255))

    def __repr__(self):
        return "<CDFrailtyStatus(frailty_status='%s', frailty_status_description='%s')>" % \
                                                    (self.frailty_status,
                                                     self.frailty_status_description)

class CDTypicalPeriod(Base):
    """
    Duration of the typical period, if fixed. Should be interval data type.
    """

    __tablename__ = 'cd_typical_period'

    typical_period = Column(String(3), primary_key=True)
    typical_duration = Column(TIMESTAMP)

    def __repr__(self):
        return "<CDTypicalPeriod(typical_period='%s', typical_duration='%s')>" % \
                                                    (self.typical_period,
                                                     self.typical_duration)
