#!/bin/bash
# --------------------------------------------------------------------
#
# Version: 	010.3d.2.0.2
# Date:		20241031
#
# REQUIREMENTS:
# - installed SIPp
# - installed bash, curl, grep, awk, cut, tr
# - NG911 repository cloned
# - script is started from it's location in repository
# 
# USAGE:
# sudo bash TC_LIS_001.sh
#
# CONFIGURATION:
# - all parameters to be set in CONFIG section
#
# DESCRIPTION:
# Script sends HTTP with location request for HTTP_locationURI
# and checks PIDF-LO response
# Then sends SIP SUBSCRIBE to SIP_locationURI and waits for
# SIP NOTIFY with PIDF-LO response
# 
# OUTPUT:
# - print of detailed test results
#
# --------------------------------------------------------------------
#
# CONFIG
# 
SIPP="/usr/local/src/sipp-3.6.1/sipp"

HTTP_locationURI=""
SIP_locationURI=""

LIS_REQUEST_TYPE="https"
LIS_FQDN=""

HTTP_SCENARIO_PATH="../../Test_files/HTTP_messages/HTTP_HELD"
HTTP_SCENARIO_FILE="Location_request"

SIPP_SCENARIO_PATH="../../Test_files/SIPp_scenarios/SIP_SUBSCRIBE"
SIPP_SCENARIO_FILE="SIP_SUBSCRIBE_FROM_LIS.xml"

SIP_LOCAL_IP_ADDRESS=""
SIP_LOCAL_PORT=""
SIP_REMOTE_IP_ADDRESS=""
SIP_REMOTE_PORT=""

HTTP_RECEIVE_TIMEOUT="5"
SIP_RECEIVE_TIMEOUT="30"

CERT_FILE=""
KEY_FILE=""

#
# --------------------------------------------------------------------
# TEST 1 - locationURI dereference using HELD
# TEST 2 - locationURI dereference using SIP
#

TESTS=(
	"error" 
	"error"
)

LOCATION_SHAPES=(
	"Point"
	"Polygon"
   	"Circle"
   	"Ellipse"
	"ArcBand"
   	"Sphere"
	"Ellipsoid"
   	"Prism"
)


function check_final_verdict(){
	FINAL_VERDICT="pass"
	for TEST in ${TESTS[@]}; do
		if [[ "$TEST" = "error" ]]; then
			FINAL_VERDICT="error"
			break
		fi
		if [[ "$TEST" = "inconc" ]]; then
			FINAL_VERDICT="inconc"
			break
		fi
		if [[ "$TEST" = "fail" ]]; then
			FINAL_VERDICT="fail"
			break
		fi
	done
	echo $FINAL_VERDICT
}


function print_results_and_exit(){
	echo
	echo "Ending at" `date`
	echo
	echo "-- TEST RESULTS --"
	echo
	echo "TEST 1 ( ${TESTS[0]} ) - locationURI dereference using HELD"
	echo "TEST 2 ( ${TESTS[1]} ) - locationURI dereference using SIP"
	echo
	echo "-------"
	echo
	FINAL_VERDICT=$(check_final_verdict)
	echo "Test case $0 finished. Verdict: $FINAL_VERDICT"
	if [[ "$FINAL_VERDICT" = "error" ]]; then
		exit 1
	fi
	exit 0
}


function with_HTTP_locationURI(){
	if [[ "$HTTP_locationURI" == "" ]]; then
		if [[ "$SIP_locationURI" == "" ]]; then
			echo "ERROR - location URI's are not configured" >&2
			exit 1
		else
			TESTS[0]="skip"
			echo "HTTP_locationURI paremeter not configured. TEST 1 will be skipped"
		fi
	fi
}


function with_SIP_locationURI(){
	if [[ "$SIP_locationURI" == "" ]]; then
		if [[ "$HTTP_locationURI" == "" ]]; then
			echo "ERROR - location URI's are not configured" >&2
			exit 1
		else
			TESTS[1]="skip"
			echo "SIP_locationURI paremeter not configured. TEST 2 will be skipped"
		fi
	fi
}


function test_location_xml_from_file(){
	file=$1
	if [[ `grep '<?xml' $file | wc -l | tr -d ' '` = "0"  ]]; then
		echo "ERROR - XML body not found in file $file" >&2
		return 1
	fi

	if [[ `grep '<presence' $file | wc -l | tr -d ' '` = "0" ]]; then
		echo "ERROR - XML body does not contain PIDF-LO in file $file" >&2
		return 1
	fi

	if [[ `grep '<location-info' $file | wc -l | tr -d ' '` = "0" ]]; then
		echo "ERROR - location-info not found in file $file" >&2
		return 1
	fi
	shape_found=false
	for shape in "${LOCATION_SHAPES[@]}"; do
		if [[ `grep $shape $file | wc -l | tr -d ' '` != "0" ]]; then
			shape_found=true
		fi
	done
	if ! $shape_found; then
		echo "ERROR - valid location shape not found in file $file" >&2
		return 1
	fi
	echo "pass"
}


function run_sipp_and_return_logfile_name(){
	if [[ $CERT_FILE = "" ]]; then
		pid=$($SIPP -t t5 -s $SIP_locationURI -sf "$SIPP_SCENARIO_PATH/$SIPP_SCENARIO_FILE" -i "$SIP_LOCAL_IP_ADDRESS:$SIP_LOCAL_PORT" "$SIP_REMOTE_IP_ADDRESS:$SIP_REMOTE_PORT" -trace_msg -timeout "$SIP_RECEIVE_TIMEOUT" -max_recv_loops 1 -m 4 -bg & >> /dev/null)
	else
		pid=$($SIPP -t l5 -tls_cert $CERT_FILE -tls_key $KEY_FILE -s $SIP_locationURI -sf "$SIPP_SCENARIO_PATH/$SIPP_SCENARIO_FILE" -i "$SIP_LOCAL_IP_ADDRESS:$SIP_LOCAL_PORT" "$SIP_REMOTE_IP_ADDRESS:$SIP_REMOTE_PORT" -trace_msg -timeout "$SIP_RECEIVE_TIMEOUT" -max_recv_loops 1 -m 4 -bg & >> /dev/null)
	fi
	sleep $SIP_RECEIVE_TIMEOUT
	pid=`echo $pid | sed 's/.*\[\(.*\)\].*/\1/'`
	scenario_name=`echo $SIPP_SCENARIO_FILE | cut -d . -f 1`
	sip_msg_file=`ls "$scenario_name"_*_messages.log`
	mv $sip_msg_file "${scenario_name}.log"
	sip_msg_file="${scenario_name}.log"
	kill -9 $PID 2> /dev/null
	echo $sip_msg_file
}


function when_SIP_SUBSCRIBE_is_sent_to_LIS(){
	if [[ "${TESTS[1]}" = "skip" ]]; then
		return 1
	fi
	echo -n "Subscribing for location to LIS (timeout=${SIP_RECEIVE_TIMEOUT}s)..."
	SIPP_TCP_LOGFILE=$(run_sipp_and_return_logfile_name)
	echo "DONE"
}


function then_SIP_NOTIFY_from_LIS_contains_location(){
	if [[ "${TESTS[1]}" = "skip" ]]; then
		return 1
	fi
	echo -n "Verification of LIS responses ..."
		if [[ `cat $SIPP_TCP_LOGFILE` = "" ]]; then
			echo "ERROR"
			echo "ERROR - no messages found in SIPp logfile $SIPP_TCP_LOGFILE"
			TESTS[1]="error"
			return 1
		fi
		sed -n '/<?xml/,/presence>/p' $SIPP_TCP_LOGFILE > location.log
		if [[ `test_location_xml_from_file location.log` = "pass" ]]; then
			TESTS[1]="pass"
			echo "DONE"
		else
			TESTS[1]="fail"
		fi
		rm $SIPP_TCP_LOGFILE
	rm location.log
}


HTTP_MSG_FILE="HTTP_logfile.log"
HTTP_MSG_FILE_PCA_CERT="HTTP_with_PCA_cert_used_logfile.log"


function when_HTTP_HELD_is_sent_to_LIS(){
	if [[ "${TESTS[0]}" = "skip" ]]; then
		return 1
	fi
	echo -n "Sending location dereference request to LIS ... "
	XML_BODY=`cat $HTTP_SCENARIO_PATH/$HTTP_SCENARIO_FILE | sed -n '/<?xml/,$p'`
	curl -X POST "$HTTP_locationURI" -d "$XML_BODY" --max-time $HTTP_RECEIVE_TIMEOUT > $HTTP_MSG_FILE 2> /dev/null
	echo "DONE"
}


function then_HTTP_response_from_LIS_contains_location(){
	if [[ "${TESTS[0]}" = "skip" ]]; then
		return 1
	fi
	echo -n "Verification of LIS responses ..."
	if [[ `cat $HTTP_MSG_FILE` = "" ]]; then
		echo "ERROR"
		echo "ERROR - no messages found in curl logfile $HTTP_MSG_FILE"
		TESTS[0]="error"
		return 1
	fi
	if [[ `test_location_xml_from_file $HTTP_MSG_FILE` = "pass" ]]; then
		TESTS[0]="pass"
		echo "DONE"
	else
		TESTS[0]="fail"
	fi
	rm $HTTP_MSG_FILE
}


# --------------------------------------------------------------------

echo
echo $0
echo "-------"
echo "Begining at" `date`
echo

with_HTTP_locationURI
when_HTTP_HELD_is_sent_to_LIS
then_HTTP_response_from_LIS_contains_location

with_SIP_locationURI
when_SIP_SUBSCRIBE_is_sent_to_LIS
then_SIP_NOTIFY_from_LIS_contains_location

print_results_and_exit
