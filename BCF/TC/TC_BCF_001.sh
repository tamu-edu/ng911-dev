#!/bin/bash
# --------------------------------------------------------------------
#
# Version: 	010.3d.2.1.1
# Date:		2024.07.26
#
# REQUIREMENTS:
# - installed SIPp
# - installed bash, grep, awk, cut
# - NG911 repository cloned
# - script is started from it's location in repository
# 
# USAGE:
# sudo bash TC_BCF_001.sh
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
# - print of final verdict (pass/fail/inconc/error)
#
# --------------------------------------------------------------------
#
# CONFIG
#
# 
TEST_NAME="TD_BCF_001"
SIP_RECEIVE_IP_ADDRESS="10.108.0.2"
SIP_RECEIVE_PORT="5060"
SIP_RECEIVE_TIMEOUT="10"
SIP_SEND_IP_ADDRESS="10.108.0.3"
SIP_SEND_PORT="5060"
EMERGENCY_IDENTIFIER_URN_PATTERN="urn:emergency:uid:callid"
INCIDENT_TRACKING_IDENTIFIER_URN_PATTERN="urn:emergency:uid:incidentid"
STRING_ID_PATTERN="[A-Za-z0-9]{10,32}"
FQDN_PATTERN="[a-z0-9\-\.]{1,200}\.[a-z0-9\-]{2,63}"
RESOURCE_PRIORITY_PATTERN="^[[:space:]]*esnet\.1[[:space:]]*$"
SIPP_RCV_XML_SCENARIO_PATH="../../Test_files/SIPp_scenarios/SIP_RECEIVE/SIP_INVITE_RECEIVE.xml"
SIPP_SND_XML_SCENARIO_PATH="../../Test_files/SIPp_scenarios/SIP_INVITE/SIP_INVITE_EMERGENCY_SINGLE.xml"
#
# --------------------------------------------------------------------

TEST_VERDICT="error"
for ((i=0; i<7; i++)); do
	TEST+=("FAILED")
done

function print_results_and_exit () {
	echo
	echo "TEST RESULTS"
	echo "____________"
	echo
	echo "TEST 1 ( ${TEST[0]} ) - Emergency Call Identifier URN : $EMERGENCY_CALL_ID_HEADER"
	echo "TEST 2 ( ${TEST[1]} ) - Emergency Call Identifier String ID : $EMERGENCY_CALL_ID_STRING_ID"
	echo "TEST 3 ( ${TEST[2]} ) - Emergency Call Identifier FQDN : $EMERGENCY_CALL_ID_FQDN"
	echo "TEST 4 ( ${TEST[3]} ) - Incident Tracking Identifier URN : $INCIDENT_TRACKING_ID_HEADER"
	echo "TEST 5 ( ${TEST[4]} ) - Incident Tracking Identifier String ID : $INCIDENT_TRACKING_ID_STRING_ID"
	echo "TEST 6 ( ${TEST[5]} ) - Incident Tracking Identifier FQDN : $INCIDENT_TRACKING_ID_FQDN"
	echo "TEST 7 ( ${TEST[6]} ) - Resource-Priority default : $RESOURCE_PRIORITY_HEADER"
	echo
	echo "------------------------------------------------------------------------------"
	echo "Ending at" `date`
	echo
	echo -n "Removing message log file $MSG_FILE..."

	MSG_FILE=`ls SIP_INVITE_receive_*_messages.log`
	rm $MSG_FILE
	CHECK_LOG=`ls ${MSG_FILE} 2> /dev/null`

	if [[ "$CHECK_LOG" != "" ]]; then
	        echo "FAILURE"
	        TEST_VERDICT="error"
	else
	        echo "DONE"
	fi
	
	echo "------------------------------------------------------------------------------"
	echo
	echo "RESULTS"
	echo "-------"
	echo "Test case $TEST_NAME finished. Verdict: $TEST_VERDICT"

	if [[ "$TEST_VERDICT" != "fail" && "$TEST_VERDICT" != "pass" ]]; then
	        exit 1
	else
	        exit 0
	fi
}

echo "------------------------------------------------------------------------------"
echo
echo "Test script: $0"
echo "Test ID: $TEST_NAME"
echo
echo "------------------------------------------------------------------------------"
echo "Begining at" `date`
echo
echo -n "Waiting for SIPp to receive SIP message (timeout=$SIP_RECEIVE_TIMEOUT seconds)... "

sipp -t t1 -sf "$SIPP_RCV_XML_SCENARIO_PATH" -aa -i "$SIP_RECEIVE_IP_ADDRESS:$SIP_RECEIVE_PORT" -trace_msg -timeout "$SIP_RECEIVE_TIMEOUT" -max_recv_loops 1 -m 1 >> /dev/null 2> /dev/null &
sleep 1
sipp -t t1 -sf "$SIPP_SND_XML_SCENARIO_PATH" "$SIP_SEND_IP_ADDRESS:$SIP_SEND_PORT" -m 1 >> /dev/null 2> /dev/null


MSG_FILE=`ls SIP_INVITE_receive_*_messages.log`
MSG_FILE_SIZE=`ls -s SIP_INVITE_receive_*_messages.log | awk '{print $1}'`

if (($MSG_FILE_SIZE > 0)); then
	echo "SUCCESS"
else
	echo "FAILED"
	TEST_VERDICT="inconc"
	print_results_and_exit
fi

echo
echo -n "Getting header field values... "


EMERGENCY_CALL_ID_HEADER=`cat $MSG_FILE | grep Call-Info | grep urn:emergency:uid:callid  -m 1`
EMERGENCY_CALL_ID_STRING_ID=`echo $EMERGENCY_CALL_ID_HEADER | rev | cut -d ':' -f 2 | rev`
EMERGENCY_CALL_ID_FQDN=`echo $EMERGENCY_CALL_ID_HEADER | rev | cut -d ':' -f 1 | rev`

INCIDENT_TRACKING_ID_HEADER=`cat $MSG_FILE | grep Call-Info | grep urn:emergency:uid:incidentid -m 1`
INCIDENT_TRACKING_ID_STRING_ID=`echo $INCIDENT_TRACKING_ID_HEADER | rev | cut -d ':' -f 2 | rev`
INCIDENT_TRACKING_ID_FQDN=`echo $INCIDENT_TRACKING_ID_HEADER | rev | cut -d ':' -f 1 | rev`

RESOURCE_PRIORITY_HEADER=`cat $MSG_FILE | grep Resource-Priority | grep esnet -m 1 | awk '{print $2}'`

echo "DONE"
echo -n "Regex verification... "

if [[ "$EMERGENCY_CALL_ID_HEADER" =~ $EMERGENCY_IDENTIFIER_URN_PATTERN ]]; then
	TEST[0]="PASSED"
fi
if [[ "$EMERGENCY_CALL_ID_STRING_ID" =~ $STRING_ID_PATTERN ]]; then
	TEST[1]="PASSED"
fi
if [[ "$EMERGENCY_CALL_ID_FQDN" =~ $FQDN_PATTERN ]]; then
	TEST[2]="PASSED"
fi
if [[ "$INCIDENT_TRACKING_ID_HEADER" =~ $INCIDENT_TRACKING_IDENTIFIER_URN_PATTERN ]]; then
	TEST[3]="PASSED"
fi
if [[ "$INCIDENT_TRACKING_ID_STRING_ID" =~ $STRING_ID_PATTERN ]]; then
	TEST[4]="PASSED"
fi
if [[ "$INCIDENT_TRACKING_ID_FQDN" =~ $FQDN_PATTERN ]]; then
	TEST[5]="PASSED"
fi
if [[ "$RESOURCE_PRIORITY_HEADER" =~ $RESOURCE_PRIORITY_PATTERN ]]; then
	TEST[6]="PASSED"
fi

echo "DONE"

echo -n "Checking final verdict... "


for ((i=0; i<7; i++)); do
	if [[ ${TEST[i]} == "PASSED" ]]; then
		TEST_VERDICT="pass"
	else
		TEST_VERDICT="fail"
		break
	fi
done

echo "DONE"

print_results_and_exit
