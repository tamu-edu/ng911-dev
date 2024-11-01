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
# sudo bash TC_ECRF-LVF_002.sh
#
# CONFIGURATION:
# - all parameters to be set in CONFIG section
#
# DESCRIPTION:
# Script sends findService HTTP request to ECRF-LVF
# with different location types and verifies
# if findServiceResponse is sent back
#
# OUTPUT:
# - print of detailed test results
#
# --------------------------------------------------------------------
#
# CONFIG
# 
HTTP_ECRF_LVF_URI=""

HTTP_SCENARIOS_PATH="../../Test_files/HTTP_messages/HTTP_LoST"

TEST_SCENARIO_FILES=(
	"findService_geodetic_point"
	"findService_geodetic_circle"
	"findService_geodetic_ellipse"
	"findService_geodetic_arc-band"
	"findService_geodetic_polygon"
	"findService_civic_address"
)

HTTP_RECEIVE_TIMEOUT="5"

#
# --------------------------------------------------------------------
# TEST 1 - findService by point geolocation
# TEST 2 - findService by circle geolocation
# TEST 3 - findService by ellipse geolocation
# TEST 4 - findService by arc-band geolocation
# TEST 5 - findService by polygon geolocation
# TEST 6 - findService by civic address
#

TESTS=(
	"error" 
	"error"
	"error" 
	"error"
	"error"
	"error"
)

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
	echo "TEST 1 ( ${TESTS[0]} ) - findService by point geolocation"
	echo "TEST 2 ( ${TESTS[1]} ) - findService by circle geolocation"
	echo "TEST 3 ( ${TESTS[2]} ) - findService by ellipse geolocation"
	echo "TEST 4 ( ${TESTS[3]} ) - findService by arc-band geolocation"
	echo "TEST 5 ( ${TESTS[4]} ) - findService by polygon geolocation"
	echo "TEST 6 ( ${TESTS[5]} ) - findService by civic address"
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


function with_HTTP_ECRF_LVF_URI_and_configured_scenario_files(){
	if [[ "$HTTP_ECRF_LVF_URI" == "" ]]; then
		echo "ERROR - ECRF-LVF URI is not configured" >&2
		exit 1
	fi
	for (( scenario_id=0; scenario_id<${#TEST_SCENARIO_FILES[@]}; scenario_id++ )); do
		if [[ `ls $HTTP_SCENARIOS_PATH/${TEST_SCENARIO_FILES[$scenario_id]} 2> /dev/null` == "" ]]; then
			echo "ERROR - missing scenario file for Test $((scenario_id+1))" >&2
			TESTS[$scenario_id]="skip"
		fi
	done
}


function send_request_with_scenario_file(){
	scenario=$1
	echo -n "Sending to ECRF-LVF request with scenario='$scenario' ... "
	xml_body=`cat $HTTP_SCENARIOS_PATH/$scenario | sed -n '/<?xml/,$p' | tr -d '\n' | tr -d '\r'`
	output_file="$scenario.log"
	curl -X POST "$HTTP_ECRF_LVF_URI" -d "$xml_body" --max-time $HTTP_RECEIVE_TIMEOUT > $output_file 2> /dev/null
	echo "DONE"
}


function test_findServiceResponse_from_file(){
	file=$1

	if [[ `grep '<?xml' $file | wc -l | tr -d ' '` = "0"  ]]; then
		echo "ERROR - XML body not found in file $file" >&2
		return 1
	fi
	if [[ `grep '<findServiceResponse' $file | wc -l | tr -d ' '` = "0" ]]; then
		echo "ERROR - findServiceResponse not found in file $file" >&2
		return 1
	fi
	if [[ `grep '<serviceBoundary' $file | wc -l | tr -d ' '` = "0" ]]; then
		echo "ERROR - serviceBoundary not found in file $file" >&2
		return 1
	fi
	service=`grep '<service>' $file | tr -d ' ' | cut -d '>' -f2 | cut -d '<' -f1`
	if [[ "$service" = "" ]]; then
		echo "ERROR - service not found or empty in file $file" >&2
		return 1
	fi
	serviceNumber=`grep '<serviceNumber>' $file | tr -d ' ' | cut -d '>' -f2 | cut -d '<' -f1`
	if [[ $serviceNumber != "" ]]; then
		if [[ "$serviceNumber" != "911" ]]; then
			echo "ERROR - serviceNumber is not 911 in file $file" >&2
			return 1
		fi
	fi
	uri_found=false
	uri_list=`grep '<uri>' $file | tr -d ' '`
	for uri in ${uri_list[@]}; do
		uri=`echo $uri | cut -d '>' -f2 | cut -d '<' -f1`
		if [[ "$uri" =~ $SIP_URI_REGEX_PATTERN ]]; then
			uri_found=true
		fi
	done
	if ! $uri_found; then
		echo "ERROR - SIP URI not found in file $file" >&2
		return 1
	fi
	echo "pass"
}


function when_HTTP_LoST_requests_are_sent_to_ECRF_LVF(){
	for (( scenario_id=0; scenario_id<${#TEST_SCENARIO_FILES[@]}; scenario_id++ )); do
		if [[ "${TESTS[$scenario_id]}" != "skip" ]]; then
			send_request_with_scenario_file ${TEST_SCENARIO_FILES[$scenario_id]}
		fi
	done
}


function check_if_response_logfile_is_not_empty(){
	scenario=$1
	echo -n "Checking response from ECRF-LVF scenario=$scenario... "
	if [[ `cat ${scenario}.log` = "" ]]; then
		echo "ERROR - no messages found in logfile ${scenario}.log"
		return 1
	fi
}


function then_ECRF_LVF_responds_with_correct_services_list(){
	for (( scenario_id=0; scenario_id<${#TEST_SCENARIO_FILES[@]}; scenario_id++ )); do
		if [[ "${TESTS[$scenario_id]}" != "skip" ]]; then
			check_if_response_logfile_is_not_empty ${TEST_SCENARIO_FILES[$scenario_id]}
			if [[ `test_findServiceResponse_from_file ${TEST_SCENARIO_FILES[$scenario_id]}.log` = "pass" ]]; then
				TESTS[$scenario_id]="pass"
				echo "DONE"
			else
				TESTS[$scenario_id]="fail"
			fi
   			rm ${TEST_SCENARIO_FILES[$scenario_id]}.log > /dev/null
		fi
	done
}


# --------------------------------------------------------------------

echo
echo $0
echo "-------"
echo "Begining at" `date`
echo

with_HTTP_ECRF_LVF_URI_and_configured_scenario_files
when_HTTP_LoST_requests_are_sent_to_ECRF_LVF
then_ECRF_LVF_responds_with_correct_services_list

print_results_and_exit
