#!/bin/bash
set -ex

# Installing EE cli
dcos package install --cli dcos-enterprise-cli

# Get root CA
curl -k -v $(dcos config show core.dcos_url)/ca/dcos-ca.crt -o dcos-ca.crt

# Create pub / priv keys
dcos security org service-accounts keypair sa-priv.pem sa-pub.pem
chmod 400 sa-pub.pem
# Create service account (autoscaling)
dcos security org service-accounts create -p sa-pub.pem -d "autoscaling service account" autoscaling
dcos security org service-accounts show autoscaling

# Create a secret (saas) for autoscaling
# Permissive
dcos security secrets create-sa-secret sa-priv.pem autoscaling saas

# Strict
#dcos security secrets create-sa-secret --strict sa-priv.pem autoscaling saas

dcos security secrets list /

# Grant superuser permissions to autoscaling
curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:superuser/users/autoscaling/full

# Generate service login token
#dcos auth login --username=autoscaling --private-key=sa-priv.pem
#echo "Token: "
#dcos config show core.dcos_acs_token

echo "Done"
