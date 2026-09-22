#!/bin/bash
# --------------------------------------------------------------------
#
# Version: 	0.1.2
# Date:		20240612
#
# REQUIREMENTS:
# - installed SIPp
# - installed bash, grep, awk, cut
# - NG911 repository cloned
# - script is started from it's location in repository
# 
# USAGE:
# sudo bash SIPP_check_default_INVITE_from_OBCF.sh
#
# CONFIGURATION:
# - all parameters to be set in CONFIG section
#
# DESCRIPTION:
# Script runs SIPp and waits for SIP INVITE.
# Once the message is received, following header fields are checked:
# - Emergency Call Identifier
# - Incident Tracking Identifier
# - Resource Priority
#
# OUTPUT:
# - print of detailed test results
#
# --------------------------------------------------------------------
#
# CONFIG
#
# 
SIP_RECEIVE_IP_ADDRESS="127.0.0.1"
SIP_RECEIVE_PORT="5060"
SIP_RECEIVE_TIMEOUT="10"
EMERGENCY_IDENTIFIER_URN_PATTERN="urn:emergency:uid:callid"
INCIDENT_TRACKING_IDENTIFIER_URN_PATTERN="urn:emergency:uid:incidentid"
STRING_ID_PATTERN="[A-Za-z0-9]{10,32}"
FQDN_PATTERN="[a-z0-9\-\.]{1,200}\.[a-z0-9\-]{2,63}"
RESOURCE_PRIORITY_PATTERN="esnet.1"
#
# --------------------------------------------------------------------

echo
echo SIPP_check_default_INVITE_from_OBCF
echo
echo -n "Waiting for SIPp (timeout=$SIP_RECEIVE_TIMEOUT)... "

sipp -sf ../Scenarios/SIP_receive/SIP_INVITE_RECEIVE.xml -i "$SIP_RECEIVE_IP_ADDRESS:$SIP_RECEIVE_PORT" -trace_msg -timeout "$SIP_RECEIVE_TIMEOUT" -max_recv_loops 1 -bg >> /dev/null

sleep $SIP_RECEIVE_TIMEOUT

MSG_FILE=`ls SIP_INVITE_RECEIVE_*_messages.log`

if [[ "$MSG_FILE" != "" ]]; then
	echo "SUCCESS"
else
	echo "FAILED"
	exit 1
fi
echo


EMERGENCY_CALL_ID_HEADER=`cat $MSG_FILE | grep Call-Info | grep urn:emergency:uid:callid  -m 1`
EMERGENCY_CALL_ID_STRING_ID=`echo $EMERGENCY_CALL_ID_HEADER | rev | cut -d ':' -f 2 | rev`
EMERGENCY_CALL_ID_FQDN=`echo $EMERGENCY_CALL_ID_HEADER | rev | cut -d ':' -f 1 | rev`

INCIDENT_TRACKING_ID_HEADER=`cat $MSG_FILE | grep Call-Info | grep urn:emergency:uid:incidentid -m 1`
INCIDENT_TRACKING_ID_STRING_ID=`echo $INCIDENT_TRACKING_ID_HEADER | rev | cut -d ':' -f 2 | rev`
INCIDENT_TRACKING_ID_FQDN=`echo $INCIDENT_TRACKING_ID_HEADER | rev | cut -d ':' -f 1 | rev`

RESOURCE_PRIORITY_HEADER=`cat $MSG_FILE | grep Resource-Priority | grep esnet -m 1 | awk '{print $2}'`


TEST_EMERGENCY_CALL_ID_URN="FAILED"
TEST_EMERGENCY_CALL_ID_STRING_ID="FAILED"
TEST_EMERGENCY_CALL_ID_FQDN="FAILED"
TEST_INCIDENT_TRACKING_ID_URN="FAILED"
TEST_INCIDENT_TRACKING_ID_STRING_ID="FAILED"
TEST_INCIDENT_TRACKING_ID_FQDN="FAILED"
TEST_RESOURCE_PRIORITY_DEFAULT="FAILED"


if [[ "$EMERGENCY_CALL_ID_HEADER" =~ $EMERGENCY_IDENTIFIER_URN_PATTERN ]]; then
	TEST_EMERGENCY_CALL_ID_URN="PASSED"
fi
if [[ "$EMERGENCY_CALL_ID_STRING_ID" =~ $STRING_ID_PATTERN ]]; then
	TEST_EMERGENCY_CALL_ID_STRING_ID="PASSED"
fi
if [[ "$EMERGENCY_CALL_ID_FQDN" =~ $FQDN_PATTERN ]]; then
	TEST_EMERGENCY_CALL_ID_FQDN="PASSED"
fi

if [[ "$INCIDENT_TRACKING_ID_HEADER" =~ $INCIDENT_TRACKING_IDENTIFIER_URN_PATTERN ]]; then
	TEST_INCIDENT_TRACKING_ID_URN="PASSED"
fi
if [[ "$INCIDENT_TRACKING_ID_STRING_ID" =~ $STRING_ID_PATTERN ]]; then
	TEST_INCIDENT_TRACKING_ID_STRING_ID="PASSED"
fi
if [[ "$INCIDENT_TRACKING_ID_FQDN" =~ $FQDN_PATTERN ]]; then
	TEST_INCIDENT_TRACKING_ID_FQDN="PASSED"
fi

if [[ "$RESOURCE_PRIORITY_HEADER" =~ $RESOURCE_PRIORITY_PATTERN ]]; then
	TEST_RESOURCE_PRIORITY_DEFAULT="PASSED"
fi

echo
echo "-- TEST RESULTS --"
echo
echo "TEST 1 ( $TEST_EMERGENCY_CALL_ID_URN ) - Emergency Call Identifier URN : $EMERGENCY_CALL_ID_HEADER"
echo "TEST 2 ( $TEST_EMERGENCY_CALL_ID_STRING_ID ) - Emergency Call Identifier String ID : $EMERGENCY_CALL_ID_STRING_ID"
echo "TEST 3 ( $TEST_EMERGENCY_CALL_ID_FQDN ) - Emergency Call Identifier FQDN : $EMERGENCY_CALL_ID_FQDN"
echo "TEST 4 ( $TEST_INCIDENT_TRACKING_ID_URN ) - Incident Tracking Identifier URN : $INCIDENT_TRACKING_ID_HEADER"
echo "TEST 5 ( $TEST_INCIDENT_TRACKING_ID_STRING_ID ) - Incident Tracking Identifier String ID : $INCIDENT_TRACKING_ID_STRING_ID"
echo "TEST 6 ( $TEST_INCIDENT_TRACKING_ID_FQDN ) - Incident Tracking Identifier FQDN : $INCIDENT_TRACKING_ID_FQDN"
echo "TEST 7 ( $TEST_RESOURCE_PRIORITY_DEFAULT ) - Resource-Priority default : $RESOURCE_PRIORITY_HEADER"
echo

#echo "-- SIP MESSAGES --"
#echo
#cat $MSG_FILE
#echo

echo "Removing $MSG_FILE"
rm $MSG_FILE