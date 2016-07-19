# -*- coding: utf-8 -*-

"""
This file uses SQL alchemy declarative base model to create SQL Tables.

Here we define tables, relationships between tables and so on.

"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy import Column, Integer, String, Boolean, Sequence, Float, BigInteger, Table, ForeignKey, TIMESTAMP, \
    Text, TypeDecorator
from PasswordHash import PasswordHash
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
import datetime

__author__ = 'Rubén Mulero'
__copyright__ = "foo"  # we need?¿

# Global variable declarative base
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
    # user_in_role_id = Column(Integer, ForeignKey('user_in_role.id'))
    user_in_role_id = Column(String(75), ForeignKey('user_in_role.id'))
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


class InterBehaviourRiskRel(Base):
    """
    InterBehaviour < -- > Risk M2m REL
    """

    __tablename__ = 'inter_behaviour_risk_rel'

    inter_behaviour_id = Column(Integer, ForeignKey('inter_behaviour.id'), primary_key=True)
    risk_id = Column(Integer, ForeignKey('risk.id'), primary_key=True)
    risk = relationship('Risk')


class IntraActivity(Base):
    """
    Activity < -- > IntraBehaviour
    """

    __tablename__ = 'intra_activity'

    # M2M Relantionship
    activity_id = Column(Integer, ForeignKey('activity.id'), primary_key=True)
    intra_behaviour_id = Column(Integer, ForeignKey('intra_behaviour.id'), primary_key=True)
    start_interval = Column(TIMESTAMP, default=datetime.datetime.utcnow, primary_key=True)      # Defined by the user?
    end_interval = Column(TIMESTAMP, primary_key=True)                                          # Defined by the user

    intra_behaviour = relationship("IntraBehaviour")


class RiskExecutedActionRel(Base):
    """
    ExecutedAction < -- > Risk
    """

    __tablename__ = 'risk_executed_action_rel'

    executed_action_id = Column(Integer, ForeignKey('executed_action.id'), primary_key=True)
    risk_id = Column(Integer, ForeignKey('risk.id'), primary_key=True)
    risk = relationship('Risk')


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


class PilotGeriatricIndicatorRel(Base):
    """
    Pilot < -- > GeriatricIndicator
    """

    __tablename__ = 'pilot_geriatric_indicator_rel'

    pilot_id = Column(Integer, ForeignKey('pilot.id'), primary_key=True)
    geriatric_indicator_id = Column(Integer, ForeignKey('geriatric_indicator.id'), primary_key=True)
    geriatric_indicator = relationship("GeriatricIndicator")
    # Extra Values
    date = Column(TIMESTAMP, primary_key=True)


class UserInRoleGeriatricIndicatorRel(Base):
    """
    UserInRole < -- > GeriatricIndicator
    """

    __tablename__ = 'user_in_role_geriatric_indicator_rel'

    user_in_role_id = Column(String(75), ForeignKey('user_in_role.id'), primary_key=True)
    geriatric_indicator_id = Column(Integer, ForeignKey('geriatric_indicator.id'), primary_key=True)
    geriatric_indicator = relationship("GeriatricIndicator")
    # Extra Values
    date = Column(TIMESTAMP)


class GeriatricIndicatorGeriatricSubIndicatorRel(Base):
    """
    GeriatricIndicator < -- > GeriatricSubIndicator
    """

    __tablename__ = 'geriatric_indicator_geriatric_sub_indicator_rel'

    geriatric_indicator_id = Column(Integer, ForeignKey('geriatric_indicator.id'), primary_key=True)
    geriatric_sub_indicator_id = Column(Integer, ForeignKey('geriatric_sub_indicator.id'), primary_key=True)
    geriatric_sub_indicator = relationship("GeriatricSubIndicator")


# Tables
class UserInRole(Base):
    """
    This table allows to store all related data from User who makes the executed_action
    """

    __tablename__ = 'user_in_role'

    id = Column(String(75), primary_key=True)
    valid_from = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    valid_to = Column(TIMESTAMP)
    # m2m
    action = relationship("ExecutedAction")
    geriatric_indicator = relationship("UserInRoleGeriatricIndicatorRel")
    # one2many
    stake_holder_id = Column(Integer, ForeignKey('stake_holder.id'))
    pilot_id = Column(Integer, ForeignKey('pilot.id'))

    def __repr__(self):
        return "<User(id='%s', valid_from='%s'. valid_to='%s')>" % (self.id, self.valid_from, self.valid_to)


class UserInSystem(Base):
    """
    Base data of the users
    """
    __tablename__ = 'user_in_system'

    id = Column(Integer, Sequence('user_in_role_seq'), primary_key=True)
    username = Column(Text, nullable=False, unique=True)
    password = Column(Password(rounds=13), nullable=False)
    # Or specify a cost factor other than the default 13
    # password = Column(Password(rounds=10))
    # Without rounds System will use 13 rounds by default
    created_date = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    # One2Many
    stake_holder_id = Column(Integer, ForeignKey('stake_holder.id'))

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
    location_name = Column(String(75))
    indoor = Column(Boolean)
    # One2Many
    pilot_id = Column(Integer, ForeignKey('pilot.id'))

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

    # One2one
    eam = relationship("EAM", uselist=False, back_populates="activity")

    # one2many
    expected_inter_behaviour = relationship("InterBehaviour", foreign_keys='InterBehaviour.expected_activity_id')
    real_inter_behaviour = relationship("InterBehaviour", foreign_keys='InterBehaviour.real_activity_id')

    # many2many
    intra_behaviour = relationship("IntraActivity")

    def __repr__(self):
        return "<Activity(activity_name='%s')>" % self.activity_name


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
    location = relationship('Location')
    # Many2Many
    geriatric_indicator = relationship("PilotGeriatricIndicatorRel")

    def __repr__(self):
        return "<Pilot(name='%s', population_size='%s')>" % (self.name, self.population_size)


class StakeHolder(Base):
    """
    This table stores all related data of project stakeholders to identify each user with his role in the system
    """

    __tablename__ = 'stake_holder'

    id = Column(Integer, Sequence('stake_holder_seq'), primary_key=True)
    name = Column(String(25), nullable=False)
    type = Column(String(25))
    # one2many
    user_in_system = relationship('UserInSystem')
    user_in_role = relationship('UserInRole')

    def __repr__(self):
        return "<StakeHolder(name='%s', type='%s')>" % (self.name, self.type)


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
    intra_behaviour_id = Column(Integer, ForeignKey('intra_behaviour.id'))

    # many2many
    risk = relationship("InterBehaviourRiskRel")

    def __repr__(self):
        return "<InterBehaviour(deviation='%s')>" % self.deviation


class IntraBehaviour(Base):
    """
    This table contains information about spatio-temporal time intervals in activities and try to store some measures
    """

    __tablename__ = 'intra_behaviour'

    id = Column(Integer, Sequence('intra_behaviour_seq'), primary_key=True)
    mean = Column(Float(10))
    period = Column(Float(10))
    deviation = Column(Float(10))

    # one2many
    inter_behaviour = relationship("InterBehaviour")

    def __repr__(self):
        return "<IntraBehaviour(mean='%s', period='%s', deviation='%s')>" % (self.mean, self.period, self.deviation)


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


# New tables based on POLIMI Geriatrician suggestions.
class GeriatricIndicator(Base):
    """
    This table records some data about Geriatric indicators. For example an GI could be "Mobility" as a representation
    of some differnet actions related with "Mobility.

    Here we need to store some extra value like Score to helps geriatricians to have a better approach of stored data.
    """

    __tablename__ = 'geriatric_indicator'

    id = Column(Integer, Sequence('geriatric_indicator_seq'), primary_key=True)
    name = Column(String(50))
    score = Column(Integer)
    # M2M
    geriatric_sub_indicator = relationship("GeriatricIndicatorGeriatricSubIndicatorRel")

    def __repr__(self):
        return "<GeriatricIndicator(name='%s', score='%s')>" % (self.name, self.score)


class GeriatricSubIndicator(Base):
    """
    In this table is stored some sub value of Geriatric indicators. A sub values related to "Mobility"
    could be "Walking, Still, Moving, Moving across rooms" and so on.

    Like GeriatricIndicator this table has some extra values.
    """

    __tablename__ = 'geriatric_sub_indicator'

    id = Column(Integer, Sequence('geriatric_sub_indicator_seq'), primary_key=True)
    name = Column(String(50))
    score = Column(Integer)

    def __repr__(self):
        return "<SimpleLocation(name='%s', score='%s')>" % (self.name, self.score)
