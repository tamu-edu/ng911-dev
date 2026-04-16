#!/bin/bash
# --------------------------------------------------------------------
#
# Version: 	0.1.3
# Date:		20240613
#
# REQUIREMENTS:
# - installed nc
# - installed bash, grep, awk, cut
# - NG911 repository cloned
# - script is started from it's location in repository
# 
# USAGE:
# bash HTTP_check_DR_for_OSP_from_OBCF.sh
#
# CONFIGURATION:
# - all parameters to be set in CONFIG section
#
# DESCRIPTION:
# - script waits for HTTP message with configurable timeout
# - parameters from JSON body are verified
#
# OUTPUT:
# - print of detailed test results
#
# --------------------------------------------------------------------
#
# CONFIG
#
# 
HTTP_PORT="80"
HTTP_RECEIVE_TIMEOUT="10"
LOG_FILE="HTTP_check_DR_from_OBCF.log"
resolutionUri_PATTERN="/Resolutions"
timestamp_PATTERN=[0-9]{10,32}
#
# --------------------------------------------------------------------

echo
echo HTTP_check_DR_from_OBCF
echo
echo -n "Waiting for HTTP message (timeout=$SIP_RECEIVE_TIMEOUT)... "

echo -e 'HTTP/1.1 201 Discrepancy Resolution successfully created\r\nContent-Length: 0\r\n' | nc -w $HTTP_RECEIVE_TIMEOUT -lp $HTTP_PORT > $LOG_FILE

CHECK_LOG_FILE=`ls $LOG_FILE`

if [[ "$CHECK_LOG_FILE" != "" ]]; then
	echo "SUCCESS"
else
	echo "FAILED"
	exit 1
fi
echo

resolutionUri=`cat $LOG_FILE | grep '"resolutionUri"' | awk '{print $2}' | cut -d '"' -f 2`
reportType=`cat $LOG_FILE | grep '"reportType"' | awk '{print $2}' | cut -d '"' -f 2`
discrepancyReportSubmittalTimeStamp=`cat $LOG_FILE | grep '"discrepancyReportSubmittalTimeStamp"' | awk '{print $2}' | cut -d '"' -f 2`
discrepancyReportId=`cat $LOG_FILE | grep '"discrepancyReportId"' | awk '{print $2}' | cut -d '"' -f 2`
reportingAgencyName=`cat $LOG_FILE | grep '"reportingAgencyName"' | awk '{print $2}' | cut -d '"' -f 2`
reportingContactJcard=`cat $LOG_FILE | grep '"reportingContactJcard"' | awk '{print $2}' | cut -d '"' -f 2`
problemService=`cat $LOG_FILE | grep '"problemService"' | awk '{print $2}' | cut -d '"' -f 2`
problemSeverity=`cat $LOG_FILE | grep '"problemSeverity"' | awk '{print $2}' | cut -d '"' -f 2`
problemComments=`cat $LOG_FILE | grep '"problemComments"' | awk '{print $2}' | cut -d '"' -f 2`
problem=`cat $LOG_FILE | grep '"problem"' | awk '{print $2}' | cut -d '"' -f 2`
callHeader=`cat $LOG_FILE | grep '"callHeader"' | awk '{print $2}' | cut -d '"' -f 2`

TEST_resolutionUri="FAILED"
TEST_reportType="FAILED"
TEST_discrepancyReportSubmittalTimeStamp="FAILED"
TEST_discrepancyReportId="FAILED"
TEST_reportingAgencyName="FAILED"
TEST_reportingContactJcard="FAILED"
TEST_problemService="FAILED"
TEST_problemSeverity="FAILED"
TEST_problemComments="FAILED"
TEST_problem="FAILED"
TEST_callHeader="FAILED"

if [[ "$resolutionUri" =~ $resolutionUri_PATTERN ]]; then
	TEST_resolutionUri="PASSED"
fi

if [[ "$reportType" == "OriginatingService" ]]; then
	TEST_reportType="PASSED"
fi

if [[ "$discrepancyReportSubmittalTimeStamp" =~ $timestamp_PATTERN ]]; then
	TEST_discrepancyReportSubmittalTimeStamp="PASSED"
fi

if [[ "$discrepancyReportId" != "" ]]; then
	TEST_discrepancyReportId="PASSED"
fi

if [[ "$reportingAgencyName" != "" ]]; then
	TEST_reportingAgencyName="PASSED"
fi

if [[ "$reportingContactJcard" != "" ]]; then
	TEST_reportingContactJcard="PASSED"
fi

if [[ "$problemService" == "OriginatingService" ]]; then
	TEST_problemService="PASSED"
fi

if [[ "$problemSeverity" != "" ]]; then
	TEST_problemSeverity="PASSED"
fi

if [[ "$problemComments" != "" ]]; then
	TEST_problemComments="PASSED"
fi

if [[ "$problem" == "BadSIP" ]]; then
	TEST_problem="PASSED"
fi

if [[ "$callHeader" != "" ]]; then
	TEST_callHeader="PASSED"
fi


echo
echo "-- TEST RESULTS --"
echo
echo "TEST 1 ( $TEST_resolutionUri ) - resolutionUri : $resolutionUri"
echo "TEST 2 ( $TEST_reportType ) - reportType : $reportType"
echo "TEST 3 ( $TEST_discrepancyReportSubmittalTimeStamp ) - discrepancyReportSubmittalTimeStamp : $discrepancyReportSubmittalTimeStamp"
echo "TEST 4 ( $TEST_discrepancyReportId ) - discrepancyReportId : $discrepancyReportId"
echo "TEST 5 ( $TEST_reportingAgencyName ) - reportingAgencyName : $reportingAgencyName"
echo "TEST 6 ( $TEST_reportingContactJcard ) - reportingContactJcard : $reportingContactJcard"
echo "TEST 7 ( $TEST_problemService ) - problemService : $problemService"
echo "TEST 8 ( $TEST_problemSeverity ) - problemSeverity : $problemSeverity"
echo "TEST 9 ( $TEST_problemComments ) - problemComments : $problemComments"
echo "TEST 10 ( $TEST_problem ) - problem : $problem"
echo "TEST 11 ( $TEST_callHeader ) - callHeader : $callHeader"
echo

echo "Removing $LOG_FILE"
#rm $LOG_FILE