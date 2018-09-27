"""
private settings for SAML2 (SAML_CONFIG).
"""

# from os import path
import os
import saml2
import saml2.saml

from commons.private import *
windows_url = 'http://localhost:8000'

# BASEDIR = path.dirname(path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if IS_LINUX:
    base_url = ubuntu_url
    xmlsec1_dir = '/usr/bin/xmlsec1'
else:
    base_url = windows_url
    # xmlsec1_dir = path.join(path.dirname(path.dirname(BASEDIR)), 'libxmlsec', 'bin', 'xmlsec.exe')
    xmlsec1_dir = os.path.join(os.path.dirname(BASE_DIR), 'libxmlsec', 'bin', 'xmlsec.exe')

SAML_CONFIG = {
  # full path to the xmlsec1 binary programm
  # 'xmlsec_binary': '/usr/bin/xmlsec1',
  'xmlsec_binary': xmlsec1_dir,

  # your entity id, usually your subdomain plus the url to the metadata view
  # 'entityid': 'http://localhost:8000/saml2/metadata/',
  'entityid': base_url + '/saml2/metadata/',

  # directory with attribute mapping
  # 'attribute_map_dir': path.join(BASEDIR, 'attribute-maps'),
  'attribute_map_dir': os.path.join(BASE_DIR, 'saml2', 'saml_attribute_maps'),

  # this block states what services we provide
  'service': {
      # we are just a lonely SP
      'sp' : {
          'name': 'CommonSpaces at Sapienza',
          'name_id_format': saml2.saml.NAMEID_FORMAT_PERSISTENT,
          'endpoints': {
              # url and binding to the assertion consumer service view
              # do not change the binding or service name
              'assertion_consumer_service': [
                  (base_url + '/saml2/acs/',
                   saml2.BINDING_HTTP_POST),
                  ],
              # url and binding to the single logout service view
              # do not change the binding or service name
              'single_logout_service': [
                  (base_url + '/saml2/ls/',
                   saml2.BINDING_HTTP_REDIRECT),
                  (base_url + '/saml2/ls/post',
                   saml2.BINDING_HTTP_POST),
                  ],
              },

          # attributes that this project need to identify a user
          'required_attributes': ['uid'],
          # 'required_attributes': ['uid', 'mail'],

          # attributes that may be useful to have but not required
          'optional_attributes': ['eduPersonAffiliation', 'eduPersonTargetedID',],
          # 'optional_attributes': ['eppn', 'eduPersonAffiliation'],

          # in this section the list of IdPs we talk to are defined
          'idp': {
              # we do not need a WAYF service since there is
              # only an IdP defined here. This IdP should be
              # present in our metadata

              # the keys of this dictionary are entity ids
              # 'https://localhost/simplesaml/saml2/idp/metadata.php': {
              idp_url + '/metadata.php': {
                  'single_sign_on_service': {
                      # saml2.BINDING_HTTP_REDIRECT: 'https://localhost/simplesaml/saml2/idp/SSOService.php',
                      saml2.BINDING_HTTP_REDIRECT: idp_url + '/SSOService.php',
                      },
                  'single_logout_service': {
                      # saml2.BINDING_HTTP_REDIRECT: 'https://localhost/simplesaml/saml2/idp/SingleLogoutService.php',
                      saml2.BINDING_HTTP_REDIRECT: idp_url + '/SingleLogoutService.php',
                      },
                  },
              },
          },
      },

  # where the remote metadata is stored
  'metadata': {
      # 'local': [path.join(BASEDIR, 'remote_metadata.xml')],
      'remote': [{'url': idp_url + '/metadata.php', 'cert': '' }]
      },

  # set to 1 to output debugging information
  'debug': 1,

  # Signing
  # 'key_file': path.join(BASEDIR, 'mycert.key'),  # private part
  # 'cert_file': path.join(BASEDIR, 'mycert.pem'),  # public part
  'key_file': os.path.join(BASE_DIR, 'saml2', 'keys', 'up2u_cert.key'),  # private part
  'cert_file': os.path.join(BASE_DIR, 'saml2', 'keys', 'up2u_cert.pem'),  # public part

  # Encryption
  'encryption_keypairs': [{
      # 'key_file': path.join(BASEDIR, 'my_encryption_key.key'),  # private part
      # 'cert_file': path.join(BASEDIR, 'my_encryption_cert.pem'),  # public part
      'key_file': os.path.join(BASE_DIR, 'saml2', 'keys', 'up2u_cert.key'),  # private part
      'cert_file': os.path.join(BASE_DIR, 'saml2', 'keys', 'up2u_cert.pem'),  # public part
  }],

  # own metadata settings
  'contact_person': [
      {'given_name': 'Stefano',
       'sur_name': 'Lariccia',
       'company': 'Sapienza Università di Roma',
       'email_address': 'stefano.lariccia@uniroma1.it',
       'contact_type': 'administrative'},
      {'given_name': 'Giovanni',
       'sur_name': 'Toffoli',
       'company': 'LINK srl',
       'email_address': 'toffoli@linkroma.it',
       'contact_type': 'technical'},
      ],
  # you can set multilanguage information here
  'organization': {
      'name': [('Sapienza Università di Roma', 'it'), ('Sapienza University - Rome', 'en')],
      'display_name': [('Sapienza', 'it'), ('Sapienza', 'en')],
      'url': [('https://www.uniroma1.it', 'it'), ('http://en.uniroma1.it/', 'en')],
      },
  'valid_for': 24,  # how long is our metadata valid
}

SAML_DJANGO_USER_MAIN_ATTRIBUTE = 'email'
SAML_CREATE_UNKNOWN_USER = True # default
SAML_ATTRIBUTE_MAPPING = {
    'uid': ('username', ),
    'mail': ('email', ),
    'cn': ('first_name', ),
    'sn': ('last_name', ),
}
