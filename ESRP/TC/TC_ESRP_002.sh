#!/bin/bash
# --------------------------------------------------------------------
#
# Version: 	010.3d.2.0.3
# Date:		20241105
#
# REQUIREMENTS:
# - installed SIPp
# - installed bash, grep, awk, cut, tr, sed
# - NG911 repository cloned
# - script is started from it's location in repository
# 
# USAGE:
# sudo bash TC_ESRP_002.sh
#
# CONFIGURATION:
# - all parameters to be set in CONFIG section
#
# DESCRIPTION:
# For each scenario script runs two types of SIPp processes:
# - receiver - running in background waits for SIP INVITE from ESRP
# - sender - sends SIP INVITE as configured in XML scenario file
# Receiving SIP INVITE triggers testing, when all scenarios are tested
# then report is generated as following:
#
# SIP_INVITE_EMERGENCY_SINGLE.xml
# TEST 1 - adding default location PIDF-LO body 
# TEST 2 - adding Geolocation header field pointing to PIDF-LO body
#
# SIP_INVITE_location_garbled_PIDF-LO_body.xml
# TEST 3 - adding default location PIDF-LO body 
# TEST 4 - adding Geolocation header field pointing to PIDF-LO body
# TEST 5 - added Geolocation header field is a top most entry in Geolocation sequence
# TEST 6 - original Geolocation header fields were not removed
# TEST 7 - original PIDF-LO body was not removed
#
# SIP_INVITE_location_reference.xml
# TEST 8 - adding default location PIDF-LO body 
# TEST 9 - adding Geolocation header field pointing to PIDF-LO body
# TEST 10 - added Geolocation header field is a top most entry in Geolocation sequence
# TEST 11 - original Geolocation header fields were not removed
#
#
# OUTPUT:
# - print of detailed test results
#
# --------------------------------------------------------------------
#
# CONFIG
# 

SIPP="/usr/local/src/sipp-3.6.1/sipp"

SIP_SENDER_LOCAL_IP_ADDRESS=""
SIP_SENDER_LOCAL_PORT=""
SIP_SENDER_REMOTE_IP_ADDRESS=""
SIP_SENDER_REMOTE_PORT=""

SIP_SENDER_CERT_FILE=""
SIP_SENDER_KEY_FILE=""

SIP_RECEIVER_LOCAL_IP_ADDRESS=""
SIP_RECEIVER_LOCAL_PORT=""
SIP_RECEIVER_REMOTE_IP_ADDRESS=""
SIP_RECEIVER_REMOTE_PORT=""

SIP_RECEIVER_CERT_FILE=""
SIP_RECEIVER_KEY_FILE=""

SIP_SEND_TIMEOUT="2"
SIP_RECEIVE_TIMEOUT="5"

SIP_SENDER_SCENARIOS_PATH="../../Test_files/SIPp_scenarios/SIP_INVITE"

SIP_RECEIVER_SCENARIOS_PATH="../../Test_files/SIPp_scenarios/SIP_RECEIVE"

TEST_SCENARIO_SIP_RECEIVE_FILE="SIP_INVITE_RECEIVE.xml"

EXPECTED_DEFAULT_PIDF_LO="Default_PIDF_LO.xml"

#
# --------------------------------------------------------------------
#

TESTS=()

PIDF_LO_LOCATION_INFO=(
	"Point"
	"Polygon"
   	"Circle"
   	"Ellipse"
	"ArcBand"
   	"Sphere"
	"Ellipsoid"
   	"Prism"
   	"civicAddress"
   	"Dynamic"
)

FILES_GENERATED=()

CURRENT_SCENARIO=""


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
	echo "SIP_INVITE_EMERGENCY_SINGLE.xml"
	echo "TEST 1 ( ${TESTS[0]} ) - adding default location PIDF-LO body"
	echo "TEST 2 ( ${TESTS[1]} ) - adding Geolocation header field pointing to PIDF-LO body"
	echo
	echo "SIP_INVITE_location_garbled_PIDF-LO_body.xml"
	echo "TEST 3 ( ${TESTS[2]} ) - adding default location PIDF-LO body"
	echo "TEST 4 ( ${TESTS[3]} ) - adding Geolocation header field pointing to PIDF-LO body"
	echo "TEST 5 ( ${TESTS[4]} ) - added Geolocation header field is a top most entry in Geolocation sequence"
	echo "TEST 6 ( ${TESTS[5]} ) - original Geolocation header fields were not removed"
	echo "TEST 7 ( ${TESTS[6]} ) - original PIDF-LO body was not removed"
	echo
	echo "SIP_INVITE_location_reference.xml"
	echo "TEST 8 ( ${TESTS[7]} ) - adding default location PIDF-LO body"
	echo "TEST 9 ( ${TESTS[8]} ) - adding Geolocation header field pointing to PIDF-LO body"
	echo "TEST 10 ( ${TESTS[9]} ) - added Geolocation header field is a top most entry in Geolocation sequence"
	echo "TEST 11 ( ${TESTS[10]} ) - original Geolocation header fields were not removed"
	echo 
	echo "-------"
	echo
	FINAL_VERDICT=$(check_final_verdict)
	echo "Test case $0 finished. Verdict: $FINAL_VERDICT"
	for file in ${FILES_GENERATED[@]}; do
		rm $file 2> /dev/null
	done
	if [[ "$FINAL_VERDICT" = "error" ]]; then
		exit 1
	fi
	exit 0
}


function with_scenario_file(){
	scenario=$1
	if [[ `ls $SIP_RECEIVER_SCENARIOS_PATH/$TEST_SCENARIO_SIP_RECEIVE_FILE 2> /dev/null` == "" ]]; then
		echo "ERROR - missing scenario file $TEST_SCENARIO_SIP_RECEIVE_FILE" >&2
		print_results_and_exit
	fi
	if [[ `ls $SIP_SENDER_SCENARIOS_PATH/$scenario 2> /dev/null` == "" ]]; then
		echo "ERROR - missing scenario file $scenario" >&2
		CURRENT_SCENARIO="skip"
	else
		scenario_name=`echo $scenario | cut -d . -f 1`
		CURRENT_SCENARIO=$scenario_name
	fi
}


function run_sipp_scenario_as_sender_or_receiver(){
	scenario_filename=$1
	#
	# mode
	#
	# 1. sender - runs scenario and kills created SIPp process
	# 2. receiver - runs scenario and prints PID of SIPp running in background
	mode=$2 #sender/receiver

	if [[ $mode = "sender" ]]; then
		if [[ $SIP_SENDER_CERT_FILE = "" ]]; then
			pid=$($SIPP -t t1 -sf "$SIP_SENDER_SCENARIOS_PATH/${scenario_filename}" -i "$SIP_SENDER_LOCAL_IP_ADDRESS:$SIP_SENDER_LOCAL_PORT" "$SIP_SENDER_REMOTE_IP_ADDRESS:$SIP_SENDER_REMOTE_PORT" -trace_msg -max_recv_loops 1 -m 1 2> /dev/null >> /dev/null )
		else
			pid=$($SIPP -t l1 -tls_cert $SIP_SENDER_CERT_FILE -tls_key $SIP_SENDER_KEY_FILE -sf "$SIP_SENDER_SCENARIOS_PATH/${scenario_filename}" -i "$SIP_SENDER_LOCAL_IP_ADDRESS:$SIP_SENDER_LOCAL_PORT" "$SIP_SENDER_REMOTE_IP_ADDRESS:$SIP_SENDER_REMOTE_PORT" -trace_msg -max_recv_loops 1 -m 1 -tls_version 1.2 -bg & >> /dev/null) 
		fi
	else
		if [[ $SIP_RECEIVER_CERT_FILE = "" ]]; then
			pid=$($SIPP -t t1 -sf "$SIP_RECEIVER_SCENARIOS_PATH/${scenario_filename}" -i "$SIP_RECEIVER_LOCAL_IP_ADDRESS:$SIP_RECEIVER_LOCAL_PORT" "$SIP_RECEIVER_REMOTE_IP_ADDRESS:$SIP_RECEIVER_REMOTE_PORT" -trace_msg -max_recv_loops 1 -m 1 -bg & >> /dev/null)
		else
			pid=$($SIPP -t l1 -tls_cert $SIP_RECEIVER_CERT_FILE -tls_key $SIP_RECEIVER_KEY_FILE -sf "$SIP_RECEIVER_SCENARIOS_PATH/${scenario_filename}" -i "$SIP_RECEIVER_LOCAL_IP_ADDRESS:$SIP_RECEIVER_LOCAL_PORT" "$SIP_RECEIVER_REMOTE_IP_ADDRESS:$SIP_RECEIVER_REMOTE_PORT" -trace_msg -max_recv_loops 1 -m 1 -tls_version 1.2 -bg & >> /dev/null)
		fi
	fi
	pid=`echo $pid | sed 's/.*\[\(.*\)\].*/\1/'`
	scenario_name=`echo $scenario_filename | cut -d . -f 1`
	sip_msg_file=`ls "$scenario_name"_*_messages.log`
	if [[ $mode = "sender" ]]; then
		mv $sip_msg_file "${scenario_name}_sender.log"
	else
		mv $sip_msg_file "${CURRENT_SCENARIO}.log"
		echo "$pid"
	fi
	return 0
}


function when_SIP_scenario_is_sent_and_received_response(){
	if [[ $CURRENT_SCENARIO = "skip" ]]; then
		return 1
	fi
	scenario_name=`echo $CURRENT_SCENARIO | cut -d . -f1`
	echo -n "Starting SIPp receiver process (scenario=${TEST_SCENARIO_SIP_RECEIVE_FILE})..."
	sipp_receiver_pid=`run_sipp_scenario_as_sender_or_receiver ${TEST_SCENARIO_SIP_RECEIVE_FILE} receiver`
	echo "DONE"
	FILES_GENERATED+=("${CURRENT_SCENARIO}.log")
	echo -n "Running SIPp sender process (scenario=${CURRENT_SCENARIO}.xml)..."
	run_sipp_scenario_as_sender_or_receiver ${CURRENT_SCENARIO}.xml sender
	sleep $SIP_SEND_TIMEOUT
	echo "DONE"
	FILES_GENERATED+=("${CURRENT_SCENARIO}_sender.log")
	echo -n "Waiting for SIPp to receive messages and stop (timeout=${SIP_RECEIVE_TIMEOUT}s, scenario=${TEST_SCENARIO_SIP_RECEIVE_FILE})..."
	sleep $SIP_RECEIVE_TIMEOUT
	kill -9 $sipp_receiver_pid 2> /dev/null
	echo "DONE"
}


function check_if_file_contains_another(){
	file_tested=$1
	file_content_source=$2
	match_found=false

	first_line_to_find=`head -n1 $file_content_source`
	lines_of_source_file=`cat $file_content_source | awk 'END {print NR}'`
	lines_with_first_line=`grep -n "$first_line_to_find" $file_tested | cut -d ':' -f1`

	current_line=1
	checked_lines=0
	lines_match=0
	start_check=false
	while IFS= read -r line; do
		for start_line in $lines_with_first_line; do
			if [[ $current_line = $start_line ]]; then
				checked_lines=0
				lines_match=0
				start_check=true
			fi
		done
		if $start_check; then
			if [[ $checked_lines -lt $lines_of_source_file ]]; then
				source_line=`sed -n "$((checked_lines+1))p" $file_content_source | tr -d '\n' | tr -d '\r'`
				current_line_to_check=`echo $line | tr -d '\n' | tr -d '\r'`
				if [[ "$current_line_to_check" = "$source_line" ]]; then
					((lines_match++))
				fi
				((checked_lines++))
			else
				start_check=false
				if [[ "$lines_match" = "$lines_of_source_file" ]]; then
					match_found=true
				fi
				lines_match=0
			fi
		fi
		((current_line++))
	done < "$file_tested"
	echo $match_found
}


function then_SIP_INVITE_received_contains_default_PIDF_LO(){
	if [[ $CURRENT_SCENARIO = "skip" ]]; then
		TESTS+=("skip")
		return 1
	else
		TESTS+=("error")
	fi
 	if [[ `grep "SIP" ${CURRENT_SCENARIO}.log` = "" ]]; then
		echo "ERROR - SIP response not found TEST ${#TESTS[@]} = error" >&2
		return 1
	fi
	cat $EXPECTED_DEFAULT_PIDF_LO | tr -d ' ' > DEFAULT_PIDF_FILE.tmp
	cat ${CURRENT_SCENARIO}.log | tr -d ' ' > SCENARIO_PIDF_FILE.tmp
	sed -i '/timestamp/d' DEFAULT_PIDF_FILE.tmp
	sed -i '/timestamp/d' SCENARIO_PIDF_FILE.tmp
	if `check_if_file_contains_another SCENARIO_PIDF_FILE.tmp DEFAULT_PIDF_FILE.tmp`; then
		TESTS[${#TESTS[@]}-1]="pass"
	else
		TESTS[${#TESTS[@]}-1]="fail"
	fi
	rm DEFAULT_PIDF_FILE.tmp
	rm SCENARIO_PIDF_FILE.tmp
}


function then_SIP_INVITE_received_contains_Geolocation_pointing_to_PIDF_LO(){
	if [[ $CURRENT_SCENARIO = "skip" ]]; then
		TESTS+=("skip")
		return 1
	else
		TESTS+=("error")
	fi
 	if [[ `grep "SIP" ${CURRENT_SCENARIO}.log` = "" ]]; then
		echo "ERROR - SIP response not found TEST ${#TESTS[@]} = error" >&2
		return 1
	fi
	original_geolocation_header_fields=`cat ${CURRENT_SCENARIO}_sender.log | grep "Geolocation" | awk '{print $2}'`
	received_geolocation_header_fields=`cat ${CURRENT_SCENARIO}.log | grep "Geolocation" | awk '{print $2}' | sed 's/^<cid://' | cut -d '>' -f1 | cut -d '<' -f2`
	content_id_found=false
	for cid in $received_geolocation_header_fields; do
		if [[ "$original_geolocation_header_fields" = *"$cid"* ]]; then
			continue
		fi
		content_id=`cat ${CURRENT_SCENARIO}.log | grep "Content-ID:" | awk '{print $2}' | cut -d '>' -f1 | cut -d '<' -f2 | grep -F "$cid"`
		if [[ $content_id != "" ]]; then
			content_id_found=true
		fi
	done
	if $content_id_found; then
		TESTS[${#TESTS[@]}-1]="pass"
	else
		TESTS[${#TESTS[@]}-1]="fail"
	fi
}


function then_SIP_INVITE_received_contains_Geolocation_added_on_top(){
	if [[ $CURRENT_SCENARIO = "skip" ]]; then
		TESTS+=("skip")
		return 1
	else
		TESTS+=("error")
	fi
 	if [[ `grep "SIP" ${CURRENT_SCENARIO}.log` = "" ]]; then
		echo "ERROR - SIP response not found TEST ${#TESTS[@]} = error" >&2
		return 1
	fi
	original_geolocation_header_fields=`cat ${CURRENT_SCENARIO}_sender.log | grep "Geolocation" | awk '{print $2}'`
	Geolocation_on_top_received_SIP_INVITE=`cat ${CURRENT_SCENARIO}.log | grep -m1 "Geolocation" | awk '{print $2}' | tr -d '\n' | tr -d '\r' | tr -d ' '`
	for original_geolocation in $original_geolocation_header_fields; do
		original_geolocation=`echo $original_geolocation | tr -d '\n' | tr -d '\r' | tr -d ' '`
		if [[ `echo $Geolocation_on_top_received_SIP_INVITE | grep -F "$original_geolocation" | tr -d ' '` != "" ]]; then
			TESTS[${#TESTS[@]}-1]="fail"
			return 1
		fi
	done
	TESTS[${#TESTS[@]}-1]="pass"
}


function then_SIP_INVITE_received_contains_original_Geolocation(){
	if [[ $CURRENT_SCENARIO = "skip" ]]; then
		TESTS+=("skip")
		return 1
	else
		TESTS+=("error")
	fi
 	if [[ `grep "SIP" ${CURRENT_SCENARIO}.log` = "" ]]; then
		echo "ERROR - SIP response not found TEST ${#TESTS[@]} = error" >&2
		return 1
	fi
	original_geolocation_header_fields=`cat ${CURRENT_SCENARIO}_sender.log | grep "Geolocation" | awk '{print $2}'`
	for original_geolocation in $original_geolocation_header_fields; do
		if [[ `cat ${CURRENT_SCENARIO}.log | grep -F "$original_geolocation" | tr -d '\n' | tr -d '\r' | tr -d ' '` = "" ]]; then
			TESTS[${#TESTS[@]}-1]="fail"
			return 1
		fi
	done
	TESTS[${#TESTS[@]}-1]="pass"
}


function then_SIP_INVITE_received_contains_original_PIDF_LO(){
	if [[ $CURRENT_SCENARIO = "skip" ]]; then
		TESTS+=("skip")
		return 1
	else
		TESTS+=("error")
	fi
 	if [[ `grep "SIP" ${CURRENT_SCENARIO}.log` = "" ]]; then
		echo "ERROR - SIP response not found TEST ${#TESTS[@]} = error" >&2
		return 1
	fi
	rm original_PIDF_LO.tmp 2> /dev/null
	while IFS= read -r line; do
		if [[ "$line" =~ [a-zA-Z0-9] ]]; then
			echo $line >> original_PIDF_LO.tmp
		else
			if [[ `grep "</" original_PIDF_LO.tmp | tr -d ' '` != "" ]]; then
				cat original_PIDF_LO.tmp | tr -d ' ' > original_PIDF_LO.tmp
				break
			else
				rm original_PIDF_LO.tmp
			fi
		fi
	done < ${CURRENT_SCENARIO}_sender.log
	cat ${CURRENT_SCENARIO}.log | tr -d ' ' > received_PIDF_LO.tmp
	if `check_if_file_contains_another received_PIDF_LO.tmp original_PIDF_LO.tmp`; then
		TESTS[${#TESTS[@]}-1]="pass"
	else
		TESTS[${#TESTS[@]}-1]="fail"
	fi
	rm original_PIDF_LO.tmp
	rm received_PIDF_LO.tmp
}


# --------------------------------------------------------------------

echo
echo $0
echo "-------"
echo "Begining at" `date`
echo

with_scenario_file "SIP_INVITE_EMERGENCY_SINGLE.xml"
when_SIP_scenario_is_sent_and_received_response
then_SIP_INVITE_received_contains_default_PIDF_LO
then_SIP_INVITE_received_contains_Geolocation_pointing_to_PIDF_LO

with_scenario_file "SIP_INVITE_location_garbled_PIDF-LO_body.xml"
when_SIP_scenario_is_sent_and_received_response
then_SIP_INVITE_received_contains_default_PIDF_LO
then_SIP_INVITE_received_contains_Geolocation_pointing_to_PIDF_LO
then_SIP_INVITE_received_contains_Geolocation_added_on_top
then_SIP_INVITE_received_contains_original_Geolocation
then_SIP_INVITE_received_contains_original_PIDF_LO

with_scenario_file "SIP_INVITE_incorrect_geolocation_for_dereference.xml"
when_SIP_scenario_is_sent_and_received_response
then_SIP_INVITE_received_contains_default_PIDF_LO
then_SIP_INVITE_received_contains_Geolocation_pointing_to_PIDF_LO
then_SIP_INVITE_received_contains_Geolocation_added_on_top
then_SIP_INVITE_received_contains_original_Geolocation

print_results_and_exit
