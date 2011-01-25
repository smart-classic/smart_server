"""
Accounts and authentication

Ben Adida
"""

from base import *
from django.utils import simplejson
from smart.lib import utils
import RDF

##
## Accounts
##
MAX_FAILED_LOGINS = 3
UNINITIALIZED, ACTIVE, DISABLED, RETIRED = 'uninitialized', 'active', 'disabled', 'retired'

class Account(Principal):
  Meta = BaseMeta()

  account = models.OneToOneField(Principal, primary_key = True, parent_link = True)

  # secrets to create the account
  primary_secret = models.CharField(max_length=16, null=True)
  secondary_secret = models.CharField(max_length=8, null=True)

  # account's name and contact email
  given_name = models.CharField(max_length = 150, null= True)
  family_name = models.CharField(max_length = 150, null= False)
  
  department = models.CharField(max_length = 150, default="any")
  role = models.CharField(max_length = 150, default="any")
    
  contact_email = models.CharField(max_length = 300, null = False)

  @property
  def full_name(self):
    if (self.given_name == None): return self.family_name
    return self.given_name + " " + self.family_name

  # login status
  last_login_at = models.DateTimeField(auto_now_add=False, null=True)
  last_failed_login_at = models.DateTimeField(auto_now_add=False, null=True)
  total_login_count = models.IntegerField(default=0)
  failed_login_count = models.IntegerField(default=0)

  STATES = ((UNINITIALIZED, u'Uninitialized (Needs Password)'),
            (ACTIVE, u'Active'),
            (DISABLED, u'Disabled / Locked'),
            (RETIRED, u'Retired'))
  
  # keep track of the state of the user
  state = models.CharField(max_length=50, choices=STATES, default=UNINITIALIZED)
  last_state_change = models.DateTimeField(auto_now_add=False, null=True)

  def __unicode__(self):
    return 'Account %s' % self.id

  def on_successful_login(self):
    self.last_login_at = datetime.now()
    self.total_login_count += 1
    self.failed_login_count = 0
    self.save()

  def on_failed_login(self):
    self.last_failed_login_at = datetime.utcnow()
    self.failed_login_count += 1
    if self.failed_login_count >= MAX_FAILED_LOGINS:
      self.set_state(DISABLED)
    self.save()

  def set_state(self, state):
    self.state = state
    self.last_state_change = datetime.utcnow()

  def disable(self):
    self.set_state(DISABLED)

  @property
  def is_active(self):
    # FIXME: Make freeze time configurable
    # If post freeze time reset failed login count and state
    if self.last_failed_login_at and \
      datetime.utcnow() - self.last_failed_login_at > timedelta(seconds=1):
      self.set_state(ACTIVE)
      self.failed_login_count = 0
    return self.state == ACTIVE

  def forgot_password(self):
      self.generate_secrets(False)
      self.send_secret()      

  def generate_secrets(self, secondary_secret_p = True):
    self.primary_secret = utils.random_string(16)
    if secondary_secret_p:
      self.secondary_secret = utils.random_string(6, [string.digits])
    else:
      self.secondary_secret = None
    self.save()

  # email the owner of the record with the secret
  def send_secret(self):
    # mail template
    subject = utils.render_template_raw('email/secret/subject', {'account' : self}, type='txt').strip()
    body = utils.render_template_raw('email/secret/body', 
                      { 'account'  : self, 
                        'url_prefix' : settings.SMART_UI_SERVER_LOCATION,
                        'from_name'  : settings.EMAIL_SUPPORT_NAME, 
                        'from_email' : settings.EMAIL_SUPPORT_ADDRESS,
                        'full_name'  : self.full_name or self.contact_email }, 
                      type='txt')

    utils.send_mail(subject, body, 
            "\"%s\" <%s>" % (settings.EMAIL_SUPPORT_NAME, settings.EMAIL_SUPPORT_ADDRESS), 
            ["\"%s\" <%s>" % (self.full_name or self.contact_email, self.contact_email)])

  def send_welcome_email(self):
    subject = utils.render_template_raw('email/welcome/subject', {'account' : self}, type='txt').strip()
    body = utils.render_template_raw('email/welcome/body', 
                      { 'account'         : self, 
                        'full_name'       : self.full_name or self.contact_email,
                        'url_prefix'      : settings.SMART_UI_SERVER_LOCATION, 
                        'email_support_name'  : settings.EMAIL_SUPPORT_NAME,
                        'email_support_address' : settings.EMAIL_SUPPORT_ADDRESS }, 
                    type='txt')

    utils.send_mail(subject, body, settings.EMAIL_FROM_ADDRESS, [self.contact_email])

  ##
  ## password stuff. This used to be stored in this table, but now it's stored
  ## in the accountauthsystems
  ##
  @property
  def password_info(self):
    try:
      return self.auth_systems.get(auth_system=AuthSystem.PASSWORD())
    except AccountAuthSystem.DoesNotExist:
      print "No PASSWORD auth system for account."
      return None

  def _add_password_auth_system(self, username):
    self.auth_systems.get_or_create(auth_system=AuthSystem.PASSWORD(), username=username)

  def _password_params_get(self):
    if not self.password_info:
      return None
    return simplejson.loads(self.password_info.auth_parameters or 'null') or {}

  def _password_params_set(self, val):
    info = self.password_info
    info.auth_parameters = simplejson.dumps(val)
    info.save()

  password_params = property(_password_params_get, _password_params_set)

  def _password_hash_get(self):
    if self.password_params:
      return self.password_params.get('password_hash', None)
    else:
      return None

  def _password_hash_set(self, value):
    new_params = self.password_params
    new_params['password_hash'] = value
    self.password_params = new_params

  password_hash = property(_password_hash_get, _password_hash_set)
  
  def _password_salt_get(self):
    return self.password_params.get('password_salt', None)

  def _password_salt_set(self, value):
    new_params = self.password_params
    new_params['password_salt'] = value
    self.password_params = new_params

  password_salt = property(_password_salt_get, _password_salt_set)

  def set_username_and_password(self, username, password=None):
    """Setup the username and password.
  
    password can be null if we don't want to set one yet.
    """
    self._add_password_auth_system(username)
    if password:
      self.password = password
    self.save()

  def reset(self):
    self.state = UNINITIALIZED
    self.generate_secrets()
    self.save()

  def reset_password(self):
    new_password = utils.random_string(10)
    self.password = new_password
    self.save()
  
    # send the mail
    subject = utils.render_template_raw('email/password_reset/subject', {'account': self}, type='txt').strip()
    body = utils.render_template_raw('email/password_reset/body', 
                      { 'account'     : self, 
                        'url_prefix'  : settings.SMART_UI_SERVER_LOCATION, 
                        'new_password'  : new_password}, 
                      type='txt')

    utils.send_mail(subject,body, settings.EMAIL_FROM_ADDRESS, [self.contact_email])

  def to_rdf(self, model = None):
    from smart.common.util import sp, foaf, rdf

    if model == None:  m = RDF.Model()
    else: m = model
    
    n = RDF.Node(uri_string="%s/users/%s" % (utils.smart_base, self.email.encode()))
    m.append(RDF.Statement(n, rdf['type'], sp['user']))    

    try:
        gn = self.given_name or "?"
        fn = self.family_name or "?"
        
        m.append(RDF.Statement(n, foaf['givenName'], RDF.Node(literal=gn.encode())))    
        m.append(RDF.Statement(n, foaf['familyName'], RDF.Node(literal=fn.encode())))    
        m.append(RDF.Statement(n, sp['department'], RDF.Node(literal=self.department.encode())))    
        m.append(RDF.Statement(n, sp['role'], RDF.Node(literal=self.role.encode())))    
        m.append(RDF.Statement(n, foaf['mbox'], RDF.Node(literal="mailto:%s"%self.email.encode())))    
    except: pass
    
    return m

  @classmethod
  def compute_hash(cls, password, salt):
    if not (isinstance(password, str) and isinstance(salt, str)):
      try:
        salt = str(salt)
        password = str(password)
      except:
        raise Exception(' Password and Salt need to be strings')
    m = hashlib.sha256()
    m.update(salt)
    m.update(password)
    return m.hexdigest()

  def password_get(self):
    raise Exception('you cannot read the password')

  def password_set(self, new_password):
    # generate a new salt
    self.password_salt = utils.random_string(20)

    # compute the hash
    self.password_hash = self.compute_hash(new_password, self.password_salt)
    if self.state == UNINITIALIZED:
      self.set_state(ACTIVE)

  def password_check(self, password_try):
    return self.password_hash == self.compute_hash(password_try, self.password_salt)

  @property
  def default_record(self):
    return self.records_owned_by.all()[0]

  @property
  def records_administered(self):
    return self.records_owned_by

  password = property(password_get, password_set)

class AuthSystem(Object):
  short_name = models.CharField(max_length=100, unique=True)

  # is this authentication system handled internally by Indivo X?
  # otherwise externally by the Chrome App
  internal_p = models.BooleanField(default=False)

  @classmethod
  def PASSWORD(cls):
    # FIXME: memoize this
    return cls.objects.get_or_create(short_name='password', internal_p=True)[0]

class AccountAuthSystem(Object):
  account = models.ForeignKey(Account, related_name = 'auth_systems')
  auth_system = models.ForeignKey(AuthSystem)  
  username = models.CharField(max_length = 250)
  
  # json content for extra parameters
  auth_parameters = models.CharField(max_length = 2000, null = True)
  user_attributes = models.CharField(max_length = 2000, null = True)
  
  class Meta:
    app_label = APP_LABEL
    unique_together = (('auth_system', 'username'),)
