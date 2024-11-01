#!/bin/bash
# --------------------------------------------------------------------
#
# Version: 	010.3d.2.0.3
# Date:		20241031
#
# REQUIREMENTS:
# - installed bash, curl, grep, awk, cut, tr
# - NG911 repository cloned
# - script is started from it's location in repository
# 
# USAGE:
# sudo bash TC_LIS_002.sh
#
# CONFIGURATION:
# - all parameters to be set in CONFIG section
#
# DESCRIPTION:
# Script sends HTTP location request (with DEVICE_URI) for locationURI to LIS
# and checks if response contains correct URL and/or SIP URI and
# expiration time is between 30min and 24h
#
# OUTPUT:
# - print of detailed test results
#
# --------------------------------------------------------------------
#
# CONFIG
# 
HTTP_LIS_URI=""

HTTP_SCENARIO_PATH="../../Test_files/HTTP_messages/HTTP_HELD"
HTTP_SCENARIO_FILE="Location_request_for_locationURI"

DEVICE_URI=""

HTTP_RECEIVE_TIMEOUT="5"

#
# --------------------------------------------------------------------
# TEST 1 - sending locationURI on request
# TEST 2 - expiration time is between 30min and 24h
#

TESTS=(
	"error" 
	"error"
)

HTTP_MSG_FILE="curl.log"

URL_REGEX_PATTERN='^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
SIP_URI_REGEX_PATTERN='^sips?:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

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
	echo "TEST 1 ( ${TESTS[0]} ) - sending locationURI on request"
	echo "TEST 2 ( ${TESTS[1]} ) - expiration time is between 30min and 24h"
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



function with_HTTP_LIS_URI(){
	if [[ "$HTTP_LIS_URI" == "" ]]; then
		echo "ERROR - location URI is not configured" >&2
		exit 1
	fi
}



function when_HTTP_HELD_is_sent_to_LIS(){
	echo -n "Sending location request to LIS ... "
	xml_body=`cat $HTTP_SCENARIO_PATH/$HTTP_SCENARIO_FILE | sed -n '/<?xml/,$p' | sed  "s/DEVICE_URI/$DEVICE_URI/"`
	curl -X POST "$HTTP_LIS_URI" -d "$xml_body" --max-time $HTTP_RECEIVE_TIMEOUT > $HTTP_MSG_FILE 2> /dev/null
	echo "DONE"
}


function test_location_uri_from_file(){
	file=$1
	if [[ `grep '<?xml' $file | wc -l | tr -d ' '` = "0"  ]]; then
		echo "ERROR - XML body not found in file $file" >&2
		return 1
	fi
	if [[ `grep '<locationResponse' $file | wc -l | tr -d ' '` = "0" ]]; then
		echo "ERROR - XML body does not contain locationResponse in file $file" >&2
		return 1
	fi
	if [[ `grep 'locationURI>' $file | wc -l | tr -d ' '` = "0" ]]; then
		echo "ERROR - locationURI not found in file $file" >&2
		return 1
	fi
	locationURI=`sed -n 's:.*locationURI>\(.*\)</.*:\1:p' $HTTP_MSG_FILE`
	if ! [[ "$locationURI" =~ $URL_REGEX_PATTERN ]] && 
		! [[ "$locationURI" =~ $SIP_URI_REGEX_PATTERN ]]; then
		echo "ERROR - locationURI is not a valid URL or SIP URI" >&2
		return 1
	fi
	echo "pass"
}


function test_location_uri_expiration_time_from_file(){
	file=$1
	if [[ `grep 'expires=' $file | wc -l | tr -d ' '` = "0" ]]; then
		echo "ERROR - XML body does not contain 'expires=' parameter in file $file" >&2
		return 1
	fi
	expiration_time=`sed -n 's:.*expires="\(.*\)".*:\1:p' $HTTP_MSG_FILE`
	timestamp_current_date_UTC=`date -u +%s 2>/dev/null` 
	timestamp_expiration_time=`date -d "$expiration_time" +%s 2>/dev/null` 
	if [[ $timestamp_expiration_time = "" ]]; then
		echo "ERROR - expiration time not found in file $file" >&2
		return 1
	fi
	thirty_minutes=$((30 * 60))
	twenty_four_hours=$((24 * 60 * 60))
	if [[ $timestamp_expiration_time -lt $timestamp_current_date_UTC ]]; then
		echo "ERROR - locationURI has expired" >&2
		return 1
	fi
	if [[ $timestamp_expiration_time -lt $(( $timestamp_current_date_UTC + thirty_minutes )) ]]; then
		echo "ERROR - locationURI expiration time is less than 30 minutes" >&2
		return 1
	fi
	if [[ $timestamp_expiration_time -gt $(( $timestamp_current_date_UTC + twenty_four_hours )) ]]; then
		echo "ERROR - locationURI expiration time is higher than 24 hours" >&2
		return 1
	fi
	echo "pass"
}


function then_HTTP_response_from_LIS_contains_valid_locationURI(){
	echo -n "Checking if curl logfile contains LIS response ... "
	if [[ `cat $HTTP_MSG_FILE` = "" ]]; then
		echo "ERROR - no messages found in curl logfile $HTTP_MSG_FILE"
		return 1
	else
		echo "DONE"
	fi
	echo -n "Checking locationURI ... "
	if [[ `test_location_uri_from_file $HTTP_MSG_FILE` = "pass" ]]; then
		TESTS[0]="pass"
		echo "DONE"
	else
		TESTS[0]="fail"
	fi
	echo -n "Checking locationURI expiration time ... "
	if [[ `test_location_uri_expiration_time_from_file $HTTP_MSG_FILE` = "pass" ]]; then
		TESTS[1]="pass"
		echo "DONE"
	else
		TESTS[1]="fail"
	fi
	rm $HTTP_MSG_FILE
}


# --------------------------------------------------------------------

echo
echo $0
echo "-------"
echo "Begining at" `date`
echo

with_HTTP_LIS_URI
when_HTTP_HELD_is_sent_to_LIS
then_HTTP_response_from_LIS_contains_valid_locationURI


print_results_and_exit
