#! /usr/bin/env python3
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.x509.oid import ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from ipaddress import IPv4Address
from ipaddress import IPv6Address
from ipaddress import AddressValueError

import configparser

def gen_alt_name(list):
  alt_name_objs = []
  for name in list:
    try:
      addr = IPv4Address(name)
      alt_name_objs.append(x509.IPAddress(addr))
      continue
    except AddressValueError:
      pass

    try:
      addr = IPv6Address(name)
      alt_name_objs.append(x509.IPAddress(addr))
      continue
    except AddressValueError:
      pass

    alt_name_objs.append(x509.DNSName(name))
  return x509.SubjectAlternativeName(alt_name_objs)

def gen_basic_key_usage():
  return x509.KeyUsage(
    content_commitment=False,
    digital_signature=True,
    key_encipherment=True,
    data_encipherment=False,
    key_agreement=False,
    key_cert_sign=False,
    crl_sign=False,
    decipher_only=False,
    encipher_only=False
  )

def gen_extended_key_usage():
  usages = []
  usages.append(ExtendedKeyUsageOID.SERVER_AUTH)
  return x509.ExtendedKeyUsage(usages)

def gen_csr(key, subject, extensions):
  builder = x509.CertificateSigningRequestBuilder()
  builder = builder.subject_name(x509.Name(subject))
  for ext in extensions:
    builder = builder.add_extension(ext[0], critical=ext[1])
  # Sign the CSR with our private key.
  csr = builder.sign(key, hashes.SHA256(), default_backend())
  return csr

config = configparser.RawConfigParser()
config.read('config.ini')

country=config.get('DEFAULT','country');
state=config.get('DEFAULT','state');
city=config.get('DEFAULT','city');
organization=config.get('DEFAULT','organization');
common_name=config.get('DEFAULT','common_name');

subject = []
alt_names = set()

print("Now create certificate signing request. Please enter the following details")
print("Leaving it empty confirms the default values")
print("Submitting a dot clears the value")
print("\n")
tmp_country=input("Country: [" + country +"]: ")
if not tmp_country:
    subject.append(x509.NameAttribute(NameOID.COUNTRY_NAME, country))
elif tmp_country != ".":
    subject.append(x509.NameAttribute(NameOID.COUNTRY_NAME, tmp_country))

tmp_state=input("State: [" + state +"]: ")
if not tmp_state:
    subject.append(x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state))
elif tmp_state != ".":
    subject.append(x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, tmp_state))

tmp_city=input("City: [" + city +"]: ")
if not tmp_city:
  subject.append(x509.NameAttribute(NameOID.LOCALITY_NAME, city))
elif tmp_city != ".":
  subject.append(x509.NameAttribute(NameOID.LOCALITY_NAME, tmp_city))

tmp_organization=input("Organization: [" + organization +"]: ")
if not tmp_organization:
  subject.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization))
elif tmp_organization != ".":
  subject.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, tmp_organization))

cn = ""
tmp_common_name=input("Common Name: [" + common_name +"]: ")
if not tmp_common_name:
  subject.append(x509.NameAttribute(NameOID.COMMON_NAME, common_name))
  cn = common_name
elif tmp_common_name != ".":
  subject.append(x509.NameAttribute(NameOID.COMMON_NAME, tmp_common_name))
  cn = tmp_common_name

alt_names.add(cn)
print("\nEnter Alternative names")
print("Leaving it empty continues")
while True:
  name = input("Alternatvie name: ")
  if not name:
    break;
  else:
    alt_names.add(name)

key = rsa.generate_private_key(public_exponent=65537,key_size=4096,backend=default_backend())
ext_list = []
ext_list.append((gen_alt_name(alt_names), False))
ext_list.append((gen_basic_key_usage(), False))
ext_list.append((gen_extended_key_usage(), False))

csr = gen_csr(key,subject,ext_list)

with open(cn + ".key", "wb") as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.BestAvailableEncryption(b"passphrase"),
    ))

with open(cn + ".csr", "wb") as f:
    f.write(csr.public_bytes(serialization.Encoding.PEM))

