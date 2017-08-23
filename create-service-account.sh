#!/bin/bash
set -ex

if [ -z ${1+x} ]; then echo "Principal name is unset"; else echo "Principal is set to '$1'"; fi
if [ -z ${2+x} ]; then echo "Namespace is unset"; else echo "Namespace is set to '$2'"; fi

SERVICE_PRINCIPAL=$1
NAMESPACE="${2/\//%252F}"
echo $NAMESPACE

# Installing EE cli
dcos package install --cli dcos-enterprise-cli

# Get root CA
curl -k -v $(dcos config show core.dcos_url)/ca/dcos-ca.crt -o dcos-ca.crt

# Create pub / priv keys
dcos security org service-accounts keypair sa-priv.pem sa-pub.pem
chmod 400 sa-pub.pem
# Create service account (autoscaling)
dcos security org service-accounts create -p sa-pub.pem -d "autoscaling service account" $SERVICE_PRINCIPAL
dcos security org service-accounts show $SERVICE_PRINCIPAL

# Create a secret (as_secret) for autoscaling
# Permissive
dcos security secrets create-sa-secret sa-priv.pem $SERVICE_PRINCIPAL as_secret_$SERVICE_PRINCIPAL

# Strict
#dcos security secrets create-sa-secret --strict sa-priv.pem $SERVICE_PRINCIPAL saas

dcos security secrets list /

# Grant permissions to autoscaling user
#curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:superuser/users/$SERVICE_PRINCIPAL/full

curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:adminrouter:ops:mesos/users/$SERVICE_PRINCIPAL/full
curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:adminrouter:ops:slave/users/$SERVICE_PRINCIPAL/full
curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:adminrouter:service:marathon/users/$SERVICE_PRINCIPAL/full

curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" -H 'Content-Type: application/json' $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:endpoint:path:%252Fcontainers -d '{"description":""}'
curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:endpoint:path:%252Fcontainers/users/$SERVICE_PRINCIPAL/read

curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" -H 'Content-Type: application/json' $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:endpoint:path:%252Fmetrics%252Fsnapshot -d '{"description":""}'
curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:endpoint:path:%252Fmetrics%252Fsnapshot/users/$SERVICE_PRINCIPAL/read

curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" -H 'Content-Type: application/json' $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:endpoint:path:%252Fmonitor%252Fstatistics -d '{"description":""}'
curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:endpoint:path:%252Fmonitor%252Fstatistics/users/$SERVICE_PRINCIPAL/read

curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" -H 'Content-Type: application/json' $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:log -d '{"description":""}'
curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:log/users/$SERVICE_PRINCIPAL/read

curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" -H 'Content-Type: application/json' $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:service:marathon:marathon:admin:events -d '{"description":""}'
curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:service:marathon:marathon:admin:events/users/$SERVICE_PRINCIPAL/read

curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" -H 'Content-Type: application/json' $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:executor:app_id:$NAMESPACE -d '{"description":""}'
curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:executor:app_id:$NAMESPACE/users/$SERVICE_PRINCIPAL/read

curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" -H 'Content-Type: application/json' $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:sandbox:app_id:$NAMESPACE -d '{"description":""}'
curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:sandbox:app_id:$NAMESPACE/users/$SERVICE_PRINCIPAL/read

curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" -H 'Content-Type: application/json' $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:task:app_id:$NAMESPACE -d '{"description":""}'
curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:task:app_id:$NAMESPACE/users/$SERVICE_PRINCIPAL/read

curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" -H 'Content-Type: application/json' $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:executor:app_id:$NAMESPACE -d '{"description":""}'
curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:executor:app_id:$NAMESPACE/users/$SERVICE_PRINCIPAL/read

curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" -H 'Content-Type: application/json' $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:service:marathon:marathon:services:$NAMESPACE -d '{"description":""}'
curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:service:marathon:marathon:services:$NAMESPACE/users/$SERVICE_PRINCIPAL/read

curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" -H 'Content-Type: application/json' $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:service:marathon:marathon:services:$NAMESPACE -d '{"description":""}'
curl -X PUT --cacert dcos-ca.crt -H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:service:marathon:marathon:services:$NAMESPACE/users/$SERVICE_PRINCIPAL/update


# Generate service login token
#dcos auth login --username=$SERVICE_PRINCIPAL --private-key=sa-priv.pem
#echo "Token: "
#dcos config show core.dcos_acs_token

echo "Done"
