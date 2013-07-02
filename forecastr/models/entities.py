#from sqlalchemy.ext.declarative import declarative_base
#from sqlalchemy import Table, Column, sa.Integer, sa.Unicode, sa.String, sa.Text, Boolean, sa.ForeignKey, DateTime, PickleType
#from sqlalchemy.orm import backref, sa.relationship
# for versioned tables, which provide an audit trail for forensic tracking of user changes
from history_meta import Versioned
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import INET, ENUM
from savalidation import ValidationMixin
import savalidation.validators as val
from savalidation.helpers import before_flush


sa = SQLAlchemy()
# sa = SQLAlchemy(session_options = {})
#sa.session.autoflush = False
#sa.session.expire_on_commit = False


"""
"""
class Area(sa.Model):
    __tablename__ = "areas"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(96), nullable=False)


"""
"""
class Forecast(sa.Model):
    __tablename__ = "forecasts"
    id = sa.Column(sa.Integer, primary_key=True)


    """Relationships"""

    """
    Use this format when class is cast to sa.String
    """

"""
Represent a person's role in the system
"""
class Role(sa.Model):
    __tablename__ = 'roles'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String(64), unique=True)
    description = sa.Column(sa.Text)

    """
    Use this format when class is cast to string
    """
    def __repr__(self):
        return "<Role('%s', '%s', '%s')>" % (self.id, self.name, self.description)


"""
Represent people or institutions who maintain iPlant-hosted services
"""
class Maintainer(sa.Model, ValidationMixin):
    __tablename__ = "maintainers"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String(96), nullable=False, unique=True)
    notes = sa.Column(sa.Text)

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()


"""
Represent a service's maintenance message
"""
class ServiceMessage(sa.Model, ValidationMixin):
    __tablename__ = "service_messages"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    message = sa.Column(sa.Text)
    valid_from = sa.Column(sa.DateTime, nullable=False)
    expires_at = sa.Column(sa.DateTime, nullable=False)

    """Relationships"""
    # One service may have multiple messages
    service_id = sa.Column(sa.Integer, sa.ForeignKey("services.id"))

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()
    # Enforces a foreign key: no ServiceMessage without a service id. Does not
    #  look up service.id to ensure its a real service, though. @TODO
    val.validates_required('service_id', sav_event='before_exec')
    # 4 chars is enough to say "down", but that would be a not-cool move...
    val.validates_minlen('message', 4)


"""
Represent a service's actions a user may perform against it
"""
class ServiceAction(sa.Model, ValidationMixin):
    __tablename__ = "service_actions"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    # What purpose does the action serve? email, access or help.
    event = sa.Column(sa.String(96), index=True)
    # The URL to go to to initiate the desired event
    # @todo: rename to 'path'?
    url = sa.Column(sa.String(255))
    notes = sa.Column(sa.Text)

    """Relationships"""
    # One service may have multiple messages
    service_id = sa.Column(sa.Integer, sa.ForeignKey("services.id"))

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()


"""
Represent a requests by a user for service access
"""
class ServiceRequest(sa.Model, Versioned, ValidationMixin):
    __tablename__ = "service_requests"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    approval = sa.Column(sa.String(64), index=True)
    # Has it been successfully added to the user's LDAP or other back-end services?
    # One of: pending, completed, denied, failed
    status = sa.Column(sa.String(24), index=True)
    # in pgsql, we can import the INET type: from sqlalchemy.dialects import postgresql
    ip_address = sa.Column(INET())
    notes = sa.Column(sa.Text)
    # Needed for joined table inheritance
    subtype = sa.Column(sa.String(255), nullable=False)

    """Relationships"""
    #ServiceRequests have several subtypes
    __mapper_args__ = {'polymorphic_on': subtype}
    # One service request is linked to one service
    service_id = sa.Column(sa.Integer, sa.ForeignKey("services.id"))
    # One service request is linked to one account
    account_id = sa.Column(sa.Integer, sa.ForeignKey("accounts.id"))

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()
    val.validates_ipaddr('ip_address')


"""
These tables implement the single table inheritance pattern, a type of polymorphic associations.
This allows us to inherit from the service_request table, but also store service-specific
extra data.
"""

"""
Joined-Table Inheritance
"""
class AtmosphereServiceRequest(ServiceRequest):
    __tablename__ = "atmosphere_requests"
    __mapper_args__ = {'polymorphic_identity': 'atmosphere_request'}

    id = sa.Column(sa.Integer, sa.ForeignKey("service_requests.id"), primary_key=True)
    how_will_use = sa.Column(sa.Text, nullable=False)


"""
Joined-Table Inheritance
"""
class DnasubwayServiceRequest(ServiceRequest):
    __tablename__ = "dnasubway_requests"
    __mapper_args__ = {'polymorphic_identity': 'dnasubway_request'}

    id = sa.Column(sa.Integer, sa.ForeignKey("service_requests.id"), primary_key=True)
    how_will_use = sa.Column(sa.PickleType(), nullable=False)
    school_name = sa.Column(sa.String(128), nullable=True)
    school_type = sa.Column(sa.String(64), nullable=True)
    school_surrounding_area = sa.Column(sa.String(24), nullable=True)


"""
Joined-Table Inheritance
"""
class IrodsServiceRequest(ServiceRequest):
    __tablename__ = "irods_requests"
    __mapper_args__ = {'polymorphic_identity': 'irods_request'}

    id = sa.Column(sa.Integer, sa.ForeignKey("service_requests.id"), primary_key=True)
    password = sa.Column(sa.String(50), nullable=False)


"""
Represent a service offered by iPlant
"""
class Service(sa.Model, ValidationMixin):
    __tablename__ = 'services'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String(96), index=True)
    # filename only; path is supplied in the application
    icon_file = sa.Column(sa.String(64))
    # One of default or NULL
    type = sa.Column(sa.String(96), index=True)
    description = sa.Column(sa.Text)
    notes = sa.Column(sa.Text)

    """Relationships"""
    # One service has one maintainer
    maintainer_id = sa.Column(sa.Integer, sa.ForeignKey('maintainers.id'))
    maintainer = sa.relationship("Maintainer")
    # One service has many messages
    messages = sa.relationship("ServiceMessage")
    # One service has many actions
    actions = sa.relationship("ServiceAction")
    # One service has many requests
    requests = sa.relationship("ServiceRequest")

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()
    val.validates_minlen('name', 3)


"""
Join Accounts and Roles

Must be in Classic syntax, apparently...
"""
account_role =sa.Table(
    'account_role', sa.Model.metadata,
    sa.Column('account_id', sa.Integer, sa.ForeignKey('accounts.id'), primary_key=True),
    sa.Column('role_id', sa.Integer, sa.ForeignKey('roles.id'), primary_key=True),
    sa.UniqueConstraint('account_id', 'role_id')
)

"""
Join Accounts and Services
"""
account_service = sa.Table(
    'account_service', sa.Model.metadata,
    sa.Column('account_id', sa.Integer, sa.ForeignKey('accounts.id'), primary_key=True),
    sa.Column('service_id', sa.Integer, sa.ForeignKey('services.id'), primary_key=True),
    sa.UniqueConstraint('account_id', 'service_id')
)


"""
Represent a service's actions a user may perform against it
"""
class ApiAction(sa.Model, ValidationMixin):
    __tablename__ = "api_actions"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    event = sa.Column(sa.String(96), index=True)
    # @todo: rename to 'path'?
    url = sa.Column(sa.String(255))
    notes = sa.Column(sa.Text)

    """Relationships"""
    # One api may have multiple actions
    api_id = sa.Column(sa.Integer, sa.ForeignKey("apis.id"))

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()


"""
Represent keys for API clients' access
"""
class ApiClientKey(sa.Model, Versioned, ValidationMixin):
    __tablename__ = "api_client_keys"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    key = sa.Column(sa.Text, nullable=False, index=True)
    type = sa.Column(sa.String(24), index=True)
    is_revoked = sa.Column(sa.Boolean, nullable=True, index=True)
    notes = sa.Column(sa.Text, nullable=True)

    """Relationships"""
    # One key has one api_client: one-many, bidirectional from api_clients
    api_client_id = sa.Column(sa.Integer, sa.ForeignKey("api_clients.id"))

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()


"""
Represent registered clients for iPlant-exposed APIs
"""
class ApiClient(sa.Model, Versioned, ValidationMixin):
    __tablename__ = 'api_clients'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String(64), nullable=False)
    description = sa.Column(sa.Text, nullable=False)
    # Has iPlant staff approved it yet?
    # One of approved, denied, NULL
    approval = sa.Column(sa.String(64), index=True)
    # One of: add, pending, completed, failed
    status = sa.Column(sa.String(24), index=True)
    # URL to the client's project page
    url = sa.Column(sa.String(255))
    notes = sa.Column(sa.Text)
    # Required for joined table inheritance
    subtype = sa.Column(sa.String(255), nullable=False)

    """Relationships"""
    # API Clients have several subtypes
    # Required for joined table inheritance
    __mapper_args__ = {'polymorphic_on': subtype}
    # One client has multiple keys
    keys = sa.relationship("ApiClientKey", backref="api_client")
    # One client has one Api; bidirectional to Api
    api_id = sa.Column(sa.Integer, sa.ForeignKey("apis.id"))
    # One client has one account; one account has many api clients
    account_id = sa.Column(sa.Integer, sa.ForeignKey("accounts.id"))

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()


"""
Joined-Table Inheritance
"""
class TrellisApiClient(ApiClient):
    __tablename__ = "trellis_api_clients"
    __mapper_args__ = {'polymorphic_identity': 'trellis_api_client'}

    id = sa.Column(sa.Integer, sa.ForeignKey("api_clients.id"), primary_key=True)
    how_will_use = sa.Column(sa.Text, nullable=False)


"""
Represent API's exposed by iPlant
"""
class Api(sa.Model, ValidationMixin):
    __tablename__ = "apis"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String(96), index=True)
    description = sa.Column(sa.Text)
    icon_file = sa.Column(sa.String(64))
    notes = sa.Column(sa.Text)

    """Relationships"""
    # One Api has one Maintainer
    maintainer_id = sa.Column(sa.Integer, sa.ForeignKey('maintainers.id'))
    maintainer = sa.relationship("Maintainer")
    # One Api has many ApiClients; bidirectional
    clients = sa.relationship("ApiClient", backref="api")

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()


"""
Represent tokens. Tokens are used with initial validation and password updates.
Tokens do not include OAuth2, CAS or other transient tokens.
"""
class Token(sa.Model, Versioned, ValidationMixin):
    __tablename__ = "tokens"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    token = sa.Column(sa.String(32), unique=True, index=True)
    # One of validation, password
    purpose = sa.Column(sa.String(64), index=True)
    expires_at = sa.Column(sa.DateTime)
    # in pgsql, we can import the INET type: from sqlalchemy.dialects import postgresql
    ip_address = sa.Column(INET())
    # @todo: Deprecate?
    status = sa.Column(sa.String(24), index=True)

    """Relationships"""
    # One account has many tokens
    account_id = sa.Column(sa.Integer, sa.ForeignKey("accounts.id"))

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()
    val.validates_ipaddr('ip_address')


"""
One person may have multiple accounts
"""
class Account(sa.Model, Versioned, ValidationMixin):
    __tablename__ = 'accounts'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    username = sa.Column(sa.Unicode(64), unique=True)
    # Should be encoded in LDAP SHA1 modified format: {SHA1}...hash...
    password = sa.Column(sa.Unicode(64), index=True)
    # in pgsql, we can import the INET type:
    ip_address = sa.Column(INET())
    is_validated = sa.Column(sa.Boolean(), unique=False, default=False, index=True)
    notes = sa.Column(sa.Text)
    status = sa.Column(sa.String(24), index=True)

    """Relationships"""
    # One person has multiple accounts
    person_id = sa.Column(sa.Integer, sa.ForeignKey('people.id'))
    # Many accounts have many roles; unidirectional from accounts
    roles = sa.relationship("Role", secondary=account_role)
    # Many accounts have many services: unidirection from accounts
    services = sa.relationship("Service", secondary=account_service)
    # One account has many Api clients, bidirectional??
    clients = sa.relationship("ApiClient")
    # One account has many tokens
    tokens = sa.relationship("Token", backref="account")

    # Mostly for __json__()
    @property
    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'validated': self.is_validated,
            #: self.status
        }

    """
    Use this format when class is cast to sa.String
    """
    def __repr__(self):
        return "<Account('%s', '%s','%s', '%s', '%s')>" % (self.id, self.username, self.password, self.is_validated, self.status)

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()
    val.validates_ipaddr('ip_address')

    @before_flush
    def forbid__reserved_usernames(self):
        # this list is a doozey!
        if self.username in ['admin', 'admin2', 'administrator', 'admin_proxy', 'andye', 'apache', 'atmosphere', 'atmo_notify', 'bisque', 'confluence', 'condor', 'de', 'de-irods', 'edwin', 'eucalyptus', 'ipc_admin', 'iplant', 'iplant_user', 'iplantadmin', 'irods_monitor', 'jira', 'jiracli', 'ipcservices', 'manager', 'monitor_user', 'mysql', 'nagios', 'nagiosadmin', 'nobody', 'postgres', 'proxy-de-tools', 'public', 'puppet', 'quickshare', 'rods', 'rodsadmin', 'rodsBoot', 'rodsuser', 'root', 'systems', 'tomcat', 'tnrs', 'user_management', 'world']:
            self.add_validation_error('username', 'Reserved usernames are not allowed')


"""
Join Accounts and Groups with extra data, a variation of many-many

We version it to answer questions like: "When was this account added?", "When was
their role changed?"
"""
class AccountGroup(Versioned, sa.Model):
    __tablename__ = "account_group"

    account_id = sa.Column(sa.Integer, sa.ForeignKey("accounts.id"), primary_key=True)
    group_id  = sa.Column(sa.Integer, sa.ForeignKey("groups.id"), primary_key=True)

    """Relationships"""
    # One accountgroup has many accounts?
    accounts = sa.relationship("Account", backref="account_group")
    # One accountgroup has one role
    role_id = sa.Column(sa.Integer, sa.ForeignKey("roles.id"))
    role = sa.relationship("Role", backref=sa.backref("account_group", uselist=False))


"""
Represent Groups of Users
"""
class Group(Versioned, sa.Model):
    __tablename__ = "groups"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(96), nullable=False)
    # @todo: should we even have a type?
    type = sa.Column(sa.String(24), nullable=True)
    notes = sa.Column(sa.Text)

    """Relationships"""
    # Many groups have many members(accounts)
    members = sa.relationship("AccountGroup", backref="group")


"""Represent Countries

Conforms to ISO 3166: http://www.iso.org/iso/country_codes
"""
class Country(sa.Model):
    __tablename__ = 'countries'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    alpha_2 = sa.Column(sa.String(2), nullable=False)
    alpha_3 = sa.Column(sa.String(3), nullable=False)
    country_code = sa.Column(sa.String(3), nullable=False)
    region_code = sa.Column(sa.String(3), nullable=False)
    sub_region_code = sa.Column(sa.String(3), nullable=False)
    name = sa.Column(sa.String(96), nullable=False)


"""
Represent Addresses
"""
class Address(sa.Model, Versioned, ValidationMixin):
    __tablename__ = 'addresses'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String(96), nullable=True, default='default')
    type = sa.Column(sa.String(24), nullable=True, index=True, default='mailing')
    street = sa.Column(sa.Text)
    city = sa.Column(sa.Unicode(96))
    state = sa.Column(sa.Unicode(96))
    notes = sa.Column(sa.Text)

    """Relationships"""
    # One profile has one address
    country_id = sa.Column(sa.Integer, sa.ForeignKey('countries.id'))

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()


"""
Represent Email Addresses
"""
class Email(sa.Model, Versioned, ValidationMixin):
    __tablename__ = 'emails'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String(96), nullable=True)
    email = sa.Column(sa.String(96), nullable=False, unique=True)
    type = sa.Column(sa.String(24), nullable=False, index=True, default='primary')
    notes = sa.Column(sa.Text)

    """Relationships"""
    # One profile has multiple emails
    profile_id = sa.Column(sa.Integer, sa.ForeignKey("profiles.id"))

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()
    val.validates_email('email')


"""
Represent phone numbers
"""
class Phone(sa.Model, Versioned, ValidationMixin):
    __tablename__ = "phones"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String(96), nullable=True)
    # "number" is a sa.String since we must accommodate arbitrary international formats
    number = sa.Column(sa.String(20), nullable=False)
    type = sa.Column(sa.String(24), nullable=True, default='primary')
    notes = sa.Column(sa.Text)

    """Relationships"""
    # One profile has multiple phones
    profile_id = sa.Column(sa.Integer, sa.ForeignKey("profiles.id"))

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()
    val.validates_usphone('number')


"""
Represent institutions, of which people are affiliated with
"""
class Institution(sa.Model, ValidationMixin):
    __tablename__ = "institutions"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String(96), nullable=False, unique=True)
    type = sa.Column(ENUM('Academic', 'Industry', 'NGO', 'Government', 'Other', name="types"))
    demographics_served = sa.Column(ENUM('HBCU', 'HSI', 'MSI', 'PUI', 'TCU', 'Other', name="demographics"))
    notes = sa.Column(sa.Text)

    """Relationships"""
    # one institution has one address
    # in reality, they don't, but requirements seem to only want to track
    # physical location, which we could just as well say is "Mailing Address"
    address_id = sa.Column(sa.Integer, sa.ForeignKey('addresses.id'))
    address = sa.relationship("Address", backref=sa.backref("institution", uselist=False))

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()


"""
Represent a peron position at an institutional
"""
class Position(sa.Model):
    __tablename__ = "positions"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String(96), nullable=False, unique=True)
    notes = sa.Column(sa.Text)


"""
Represent groupings of a peron's institutional affiliations.
"""
class ResearchArea(sa.Model):
    __tablename__ = "research_areas"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String(96), nullable=False, unique=True)
    notes = sa.Column(sa.Text)


"""
Join ResearchAreas and Affiliations

Must be in Classic syntax
"""
affiliation_research_area =sa.Table(
    'affiliation_research_area', sa.Model.metadata,
    sa.Column('affiliation_id', sa.Integer, sa.ForeignKey('affiliations.id'), primary_key=True),
    sa.Column('research_area_id', sa.Integer, sa.ForeignKey('research_areas.id'), primary_key=True),
    sa.UniqueConstraint('affiliation_id', 'research_area_id')
)

"""
Represent groupings of a peron's institutional affiliations.

...Because, we want to ensure that multiple positions, depts & institutions are
related in some way rather than a jumble of many-many and many-one sa.relationships.
"""
class Affiliation(sa.Model, Versioned, ValidationMixin):
    __tablename__ = "affiliations"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String(96), nullable=True, default="primary")
    type = sa.Column(sa.String(24), nullable=True, index=True)
    department = sa.Column(sa.String(96), nullable=True)
    notes = sa.Column(sa.Text)

    """Relationships"""
    # One profile has one institution
    institution_id = sa.Column(sa.Integer, sa.ForeignKey("institutions.id"))
    institution = sa.relationship("Institution")
    # One affiliation has many research areas
    research_areas = sa.relationship("ResearchArea", secondary=affiliation_research_area)
    # one affiliation has one position
    position_id = sa.Column(sa.Integer, sa.ForeignKey("positions.id"))
    position = sa.relationship("Position")
    # One affiliation has multiple profiles
    profile_id = sa.Column(sa.Integer, sa.ForeignKey("profiles.id"))

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()


"""
Represent user profiles, containing changeable, non-permanent data about users, including preferences and settings.
"""
class Profile(sa.Model, Versioned, ValidationMixin):
    __tablename__ = "profiles"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String(96), nullable=True, default="default")
    type = sa.Column(sa.String(24), nullable=True, index=True)
    participate_in_survey = sa.Column(sa.Boolean, nullable=True)
    how_heard_about = sa.Column(sa.String(255), nullable=True)
    notes = sa.Column(sa.Text)

    """Relationships"""
    # one person has one profile
    person_id = sa.Column(sa.Integer, sa.ForeignKey('people.id'))
    # One profile has many emails
    emails = sa.relationship("Email", backref='profile', cascade="all, delete, delete-orphan")
    # One profile has many phones
    phones = sa.relationship("Phone", backref='profile', cascade="all, delete, delete-orphan")
    # One profile has one address
    address_id = sa.Column(sa.Integer, sa.ForeignKey('addresses.id'))
    address = sa.relationship("Address", backref=sa.backref("profile", uselist=False))
    # One profile has many affiliations
    affiliations = sa.relationship("Affiliation", backref='profile')

    """
    Use this format when class is cast to string
    """
    def __repr__(self):
        # @todo: JSONify the return sa.String
        return "<Profile('%s', '%s', '%s', '%s')>" % (self.id, self.name, self.type, self.notes)

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()


"""
Represent possible ethnicities for a person
"""
class Ethnicity(sa.Model):
    __tablename__ = 'ethnicities'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String(96), nullable=False)


"""
Join People and Countries on citizenship

Must be in Classic syntax
"""
citizenship_countries =sa.Table(
    'people_citizenship_country', sa.Model.metadata,
    sa.Column('person_id', sa.Integer, sa.ForeignKey('people.id'), primary_key=True),
    sa.Column('country_id', sa.Integer, sa.ForeignKey('countries.id'), primary_key=True),
    sa.UniqueConstraint('person_id', 'country_id')
)

"""
Join People and Countries on residency

Must be in Classic syntax
"""
residency_countries =sa.Table(
    'people_residency_country', sa.Model.metadata,
    sa.Column('person_id', sa.Integer, sa.ForeignKey('people.id'), primary_key=True),
    sa.Column('country_id', sa.Integer, sa.ForeignKey('countries.id'), primary_key=True),
    sa.UniqueConstraint('person_id', 'country_id')
)


"""
Represent a Person, which is distinct from their Profile(s) & Account(s)
"""
class Person(sa.Model, Versioned, ValidationMixin):
    __tablename__ = 'people'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    first_name = sa.Column(sa.Unicode(64), nullable=False, index=True)
    last_name = sa.Column(sa.Unicode(64), nullable=False, index=True)
    gender = sa.Column(sa.String(12), nullable=True)
    notes = sa.Column(sa.Text)

    """Relationships"""
    # one person has many accounts
    accounts = sa.relationship("Account", backref='person', cascade="all, delete, delete-orphan")
    # one person has one profile
    profile = sa.relationship("Profile", uselist=False, backref="person")
    # Many persons may have multiple citizenships & residencies
    citizenships = sa.relationship("Country", secondary=citizenship_countries)
    residencies = sa.relationship("Country", secondary=residency_countries)
    # many person have one ethnicity
    ethnicity_id = sa.Column(sa.Integer, sa.ForeignKey("ethnicities.id"))
    ethnicity = sa.relationship("Ethnicity")

    # Mostly for __json__()
    @property
    def serialize(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'gender': self.gender
        }


    """
    Use this format when class is cast to string
    """
    def __repr__(self):
        # @todo: JSONify the return sa.String
        return "<Person('%s', '%s','%s', '%s')>" % (self.id, self.first_name, self.last_name, self.gender)

    """Validation"""
    # will validate nullability and string types
    val.validates_constraints()
    val.validates_presence_of('gender')
