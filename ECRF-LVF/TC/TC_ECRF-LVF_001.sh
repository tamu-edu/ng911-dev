#!/bin/bash
# --------------------------------------------------------------------
#
# Version: 	010.3d.2.0.3
# Date:		20241014
#
# REQUIREMENTS:
# - installed bash, curl, grep, awk, cut, tr
# - NG911 repository cloned
# - script is started from it's location in repository
# 
# USAGE:
# sudo bash TC_ECRF-LVF_001.sh
#
# CONFIGURATION:
# - all parameters to be set in CONFIG section
#
# DESCRIPTION:
# Script sends listServices HTTP requests to ECRF-LVF with:
# - urn:service:sos
# - urn:emergency:service:sos
# Then sends listServicesByLocation with the same services, using
# location point from CONFIG section.
#
# OUTPUT:
# - print of detailed test results
#
# --------------------------------------------------------------------
#
# CONFIG
# 
HTTP_ECRF_LVF_URI=""

POINT_LAT=""
POINT_LON=""

HTTP_SCENARIOS_PATH="../../Test_files/HTTP_messages/HTTP_LoST"

TEST_SCENARIO_FILES=(
	"listServices_urn-service-sos"
	"listServices_urn-emergency-service-sos"
	"listServicesByLocation_urn-service-sos"
	"listServicesByLocation_urn-emergency-service-sos"
)


HTTP_RECEIVE_TIMEOUT="5"

#
# --------------------------------------------------------------------
# TEST 1 - listServices urn:service:sos
# TEST 2 - listServices urn:emergency:service:sos
# TEST 3 - listServicesByLocation urn:service:sos
# TEST 4 - listServicesByLocation urn:emergency:service:sos
#

TESTS=(
	"error" 
	"error"
	"error" 
	"error"
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
	echo "TEST 1 ( ${TESTS[0]} ) - listServices urn:service:sos"
	echo "TEST 2 ( ${TESTS[1]} ) - listServices urn:emergency:service:sos"
	echo "TEST 3 ( ${TESTS[2]} ) - listServicesByLocation urn:service:sos"
	echo "TEST 4 ( ${TESTS[3]} ) - listServicesByLocation urn:emergency:service:sos"
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


function with_HTTP_ECRF_LVF_URI_and_scenario_files(){
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
	if [[ "$POINT_LAT" == "" || "$POINT_LON" == "" ]]; then
		echo "ERROR - point coordinates not configured. Test 3 and Test 4 will be skipped" >$2
		TESTS[2]="skip"
		TESTS[3]="skip"
	fi
}


function send_request_with_scenario_file(){
	scenario=$1
	echo -n "Sending to ECRF-LVF request with scenario='$scenario' ... "
	xml_body=`cat $HTTP_SCENARIOS_PATH/$scenario | sed -n '/<?xml/,$p' | tr -d '\n' | tr -d '\t' | sed  "s/POINT_LAT/$POINT_LAT/" | sed  "s/POINT_LON/$POINT_LON/"`
	output_file="$scenario.log"
	curl -X POST "$HTTP_ECRF_LVF_URI" -d "$xml_body" --max-time $HTTP_RECEIVE_TIMEOUT > $output_file 2> /dev/null
	echo "DONE"
}


function test_listServices_response_from_file(){
	file=$1
	service_tested=$2
	by_location=$3 # by_location or empty
	if [[ `grep '<?xml' $file | wc -l | tr -d ' '` = "0"  ]]; then
		echo "ERROR - XML body not found in file $file" >&2
		return 1
	fi
	if [[ `grep 'serviceList>' $file | wc -l | tr -d ' '` = "0" ]]; then
		echo "ERROR - serviceList not found in file $file" >&2
		return 1
	fi
	services_list=`awk '/<serviceList>/{flag=1; next} /<\/serviceList>/{flag=0} flag' $file | tr -d ' '`
	if [[ "$services_list" = "" ]]; then
		echo "ERROR - list of services not found in file $file" >&2
		return 1
	fi
	services_check="pass"
	for service in ${services_list[@]}; do
		if [[ `echo $service | grep $service_tested | wc -l | tr -d ' '` = "0" ]]; then
			services_check="fail"
		fi
	done
	if [[ $services_check = "fail" ]]; then
		echo "ERROR - some entries in serviceList do not contain $service_tested in file $file" >&2
		return 1
	fi
	if [[ $by_location != "" ]]; then
		if [[ `grep '<listServicesByLocationResponse' $file | wc -l | tr -d ' '` = "0" ]]; then
			echo "ERROR - XML body does not contain listServicesByLocationResponse in file $file" >&2
			return 1
		fi
		if [[ `grep '<locationUsed id=' $file | wc -l | tr -d ' '` = "0" ]]; then
			echo "ERROR - locationUsed id is missing in file $file" >&2
			return 1
		fi
	else
		if [[ `grep '<listServicesResponse' $file | wc -l | tr -d ' '` = "0" ]]; then
			echo "ERROR - XML body does not contain listServicesResponse in file $file" >&2
			return 1
		fi
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
	else
		echo "DONE"
	fi
}


function then_ECRF_LVF_responds_with_correct_services_list(){
	for (( scenario_id=0; scenario_id<${#TEST_SCENARIO_FILES[@]}; scenario_id++ )); do
		if [[ "${TESTS[$scenario_id]}" != "skip" ]]; then
			check_if_response_logfile_is_not_empty ${TEST_SCENARIO_FILES[$scenario_id]}
			if [[ $scenario_id -eq 0 || $scenario_id -eq 2 ]]; then
				test_response_result=`test_listServices_response_from_file ${TEST_SCENARIO_FILES[$scenario_id]}.log urn:service:sos`
			else
				test_response_result=`test_listServices_response_from_file ${TEST_SCENARIO_FILES[$scenario_id]}.log urn:emergency:service:sos`
			fi
			if [[ $test_response_result = "pass" ]]; then
				TESTS[$scenario_id]="pass"
				echo "DONE"
			else
				TESTS[$scenario_id]="fail"
			fi
		fi
	done
	return 0
	rm ${TEST_1_SCENARIO_FILE}.log
	rm ${TEST_2_SCENARIO_FILE}.log
	rm ${TEST_3_SCENARIO_FILE}.log
	rm ${TEST_4_SCENARIO_FILE}.log
}


# --------------------------------------------------------------------

echo
echo $0
echo "-------"
echo "Begining at" `date`
echo

with_HTTP_ECRF_LVF_URI_and_scenario_files
when_HTTP_LoST_requests_are_sent_to_ECRF_LVF
then_ECRF_LVF_responds_with_correct_services_list

print_results_and_exit
