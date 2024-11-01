#!/bin/bash
# --------------------------------------------------------------------
#
# Version: 	010.3d.2.0.2
# Date:		20241031
#
# REQUIREMENTS:
# - installed bash, curl, grep, awk, cut, tr
# - NG911 repository cloned
# - script is started from it's location in repository
# 
# USAGE:
# sudo bash TC_ECRF-LVF_003.sh
#
# CONFIGURATION:
# - all parameters to be set in CONFIG section
#
# DESCRIPTION:
# Script sends findService HTTP requests to ECRF-LVF which have multiple
# service boundaries provisioned. Request contains polygon which covers:
# - partially one and fully another boundary
# - fully two boundaries
# Scripts checks as well recursive/iterative modes for polygon which
# does not cover boundaries of ECRF-LVF.
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
	"findService_polygon_covering_fully_one_and_partialy_another_boundary"
	"findService_polygon_covering_fully_two_boundaries"
	"findService_recursive_mode_polygon_not_covering_boundaries"
	"findService_iterative_mode_polygon_not_covering_boundaries"
)

TEST_SCENARIOS_EXPECTED_SIP_URI_RESPONSES=(
	"sip:service1@test.com"
	"any"
	"sip:service3@test.com"
	"none"
)

TEST_SCENARIO_4_EXPECTED_REDIRECT_URL=""

HTTP_RECEIVE_TIMEOUT="5"

#
# --------------------------------------------------------------------
# TEST 1 - (request=1x fully covered service boundary + 1x partially) returning service fully covered
# TEST 2 - (request=2x fully covered service boundaries) returning one of service boundaries
# TEST 3 - returning service under another ECRF jurisdiction
# TEST 4 - returning FQDN of next ECRF server
#

TESTS=(
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
	echo "TEST 1 ( ${TESTS[0]} ) - (request=1x fully covered service boundary + 1x partially) returning service fully covered"
	echo "TEST 2 ( ${TESTS[1]} ) - (request=2x fully covered service boundaries) returning one of service boundaries"
	echo "TEST 3 ( ${TESTS[2]} ) - returning service under another ECRF jurisdiction"
	echo "TEST 4 ( ${TESTS[3]} ) - returning FQDN of next ECRF server"
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


function with_HTTP_ECRF_LVF_URI_and_scenario_files_and_expected_responses_list(){
	if [[ "$HTTP_ECRF_LVF_URI" == "" ]]; then
		echo "ERROR - ECRF-LVF URI is not configured" >&2
		exit 1
	fi
	for (( scenario_id=0; scenario_id<${#TEST_SCENARIO_FILES[@]}; scenario_id++ )); do
		if [[ ${TEST_SCENARIO_FILES[$scenario_id]} = "any" ]]; then
			continue
		fi
		if [[ ${TEST_SCENARIO_FILES[$scenario_id]} = "none" ]]; then
			continue
		fi
		if [[ `ls $HTTP_SCENARIOS_PATH/${TEST_SCENARIO_FILES[$scenario_id]} 2> /dev/null` == "" ]]; then
			echo "ERROR - missing scenario file for Test $((scenario_id+1))" >&2
			TESTS[$scenario_id]="skip"
		fi
	done
	if [[ "$TEST_SCENARIO_4_EXPECTED_REDIRECT_URL" == "" ]]; then
		echo "ERROR - expected redirect URL for TEST 4 is not configured" >&2
		exit 1
	fi
}


function send_request_with_scenario_file(){
	scenario=$1
	echo -n "Sending to ECRF-LVF request with scenario='$scenario' ... "
	xml_body=`cat $HTTP_SCENARIOS_PATH/$scenario | sed -n '/<?xml/,$p' | tr -d '\n' | tr -d '\t'`
	output_file="$scenario.log"
	if [[ "$scenario" = "${TEST_SCENARIO_FILES[3]}" ]]; then
		curl -L -I "$HTTP_ECRF_LVF_URI" --max-time $HTTP_RECEIVE_TIMEOUT > $output_file 2> /dev/null
	else
		curl -X POST "$HTTP_ECRF_LVF_URI" -d "$xml_body" --max-time $HTTP_RECEIVE_TIMEOUT > $output_file 2> /dev/null
	fi
	echo "DONE"
}


function test_findServiceResponse_from_file_with_sip_uri_check(){
	file=$1
	expected_sip_uri=$2

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
	uri_found=false
	expected_sip_uri_found=false
	uri_list=`grep '<uri>' $file | tr -d ' '`
	for uri in ${uri_list[@]}; do
		uri=`echo $uri | cut -d '>' -f2 | cut -d '<' -f1`
		if [[ "$uri" =~ $SIP_URI_REGEX_PATTERN ]]; then
			uri_found=true
			if [[ "$uri" = "$expected_sip_uri" ]]; then
				expected_sip_uri_found=true
			elif [[ "$expected_sip_uri" = "any" ]]; then
				expected_sip_uri_found=true
			fi
		fi
	done
	if ! $uri_found; then
		echo "ERROR - SIP URI not found in file $file" >&2
		return 1
	fi
	if ! $expected_sip_uri_found; then
		echo "ERROR - expected SIP URI ($expected_sip_uri) not found in file $file" >&2
		return 1
	fi
	echo "pass"
}


function test_redirect_location_url_present_in_file(){
	file=$1
	redirect_URL=`grep "Location: " $file | awk '{print $2}' | tr -d '\n' | tr -d '\r'`
	if [[ "$redirect_URL" != "$TEST_SCENARIO_4_EXPECTED_REDIRECT_URL" ]]; then
		echo "ERROR - expected redirect Location URL ($TEST_SCENARIO_4_EXPECTED_REDIRECT_URL) not found in file $file" >&2
		return 1
	else
		echo "pass"
	fi
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


function then_ECRF_LVF_responds_with_correct_services_list_or_redirect_URL(){
	for (( scenario_id=0; scenario_id<${#TEST_SCENARIO_FILES[@]}; scenario_id++ )); do
		if [[ "${TESTS[$scenario_id]}" != "skip" ]]; then
			check_if_response_logfile_is_not_empty ${TEST_SCENARIO_FILES[$scenario_id]}
			if ! [[ $scenario_id -eq 3 ]]; then
				result_test_findResponse=`test_findServiceResponse_from_file_with_sip_uri_check ${TEST_SCENARIO_FILES[$scenario_id]}.log ${TEST_SCENARIOS_EXPECTED_SIP_URI_RESPONSES[$scenario_id]}`
				if [[ $result_test_findResponse = "pass" ]]; then
					TESTS[$scenario_id]="pass"
					echo "DONE"
				else
					TESTS[$scenario_id]="fail"
				fi
			else
				result_test_redirect_URL=`test_redirect_location_url_present_in_file ${TEST_SCENARIO_FILES[$scenario_id]}.log`
				if [[ $result_test_redirect_URL = "pass" ]]; then
					TESTS[$scenario_id]="pass"
					echo "DONE"
				else
					TESTS[$scenario_id]="fail"
				fi
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

with_HTTP_ECRF_LVF_URI_and_scenario_files_and_expected_responses_list
when_HTTP_LoST_requests_are_sent_to_ECRF_LVF
then_ECRF_LVF_responds_with_correct_services_list_or_redirect_URL

print_results_and_exit
