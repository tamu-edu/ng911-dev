#!/bin/bash
# --------------------------------------------------------------------
#
# Version: 	010.3d.0.0.7
# Date:		2024.08.29
#
# REQUIREMENTS:
# - installed bash, grep, sed, cut, wc, awk, uniq, sort
# 
# USAGE:
# bash verify_config.sh <config_file_path>
#
# DESCRIPTION:
# Script performs verification of config file to be used
# by NG911 Test Suite.
#
# OUTPUT:
# Variant1 - "Verification of config file: <config_file>... PASSED"
#
# Variant2 - 
# "Verification of config file: <config_file> ... FAILED"
# + detailed information about issues found, for example:
#
# [Line 64] ERROR - Read file error: o-bcf_test_com_key.pem for: IF_2_KEY
# [Line 73] ERROR - Certificate and private key files do not match for IF_3_CERT and IF_3_KEY
#
# --------------------------------------------------------------------
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <config_file>"
  exit 1
fi

CONFIG_FILE=$1

IUT_VARIABLES=(
	IUT_NAME
	IUT_DESCRIPTION
	IUT_TYPE
	IUT_VENDOR
	IUT_SW_VERSION
	IUT_HW_VERSION
	IUT_FQDN
	)


IF_VARIABLES=(
	IF_[ID]_NAME
	IF_[ID]_IP_ADDRESS
	IF_[ID]_SUBNET_MASK
	IF_[ID]_GATEWAY_IP_ADDRESS
	IF_[ID]_MAC_ADDRESS
	IF_[ID]_PROTOCOLS
	IF_[ID]_TRANSPORTS
	IF_[ID]_CERT
	)


IUT_TYPES=(
	BCF
	ESRP
	ECRF-LVF
	LIS
	ADR
	LS
	PS
	CHE
	)


ERRORS=()
WARNINGS=()


function add_report(){
	variable=$1
	type=$2
	message=$3
	lines=`cat $CONFIG_FILE | grep "^$variable" -w -n -o | cut -d '=' -f 1 | cut -d ':' -f 1 `
	for line in $lines; do
		if [[ "$type" == "warning" ]]; then
			WARNINGS+=("[Line $line] WARNING - $message")
		else
			ERRORS+=("[Line $line] ERROR - $message")
		fi
	done
	if [[ "$lines" == "" ]]; then
		if [[ "$type" == "warning" ]]; then
			WARNINGS+=("[Line #] WARNING - $message")
		else
			ERRORS+=("[Line #] ERROR - $message")
		fi
	fi
}


function verify_iut_type(){
	variable=$1
	value=$2
	if ! [[ ${IUT_TYPES[@]} =~ $value ]]; then
		add_report $variable error "Incorrect IUT_TYPE: $value"
	fi
}


function verify_if_name(){
	variable=$1
	value=$2
	iut_name=`cat $CONFIG_FILE | grep "IUT_NAME" -w | sed '/^#/d' | sed 's/.*=//' | sed "s/[\'\"]//g"`
	if_name_pattern=`echo "^IF_.*$"`
	if ! [[ $value =~ $if_name_pattern ]]; then
		add_report $variable error "Incorrect interface name format for: $variable"
	fi
	if_name_source_dut_pattern=`echo "^IF_"$iut_name"_.*$"`
	if ! [[ $value =~ $if_name_source_dut_pattern ]]; then
		add_report $variable error "Incorrect IUT source in interface name for: $variable - should be the same as IUT_NAME"
	fi
}


function verify_ip_address(){
	variable=$1
	value=$2
	ipv4_pattern="^([0-9]{1,3}\.){3}[0-9]{1,3}$"
	if ! [[ $value =~ $ipv4_pattern ]]; then
		add_report $variable error "Incorrect IP address value set for variable: $variable"
		return -1
	fi
	return 0
}


function verify_fqdn(){
	variable=$1
	value=$2
	fqdn_pattern="^([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+[a-zA-Z]{2,63}$"
	if ! [[ $value =~ $fqdn_pattern ]]; then
		add_report $variable error "Incorrect FQDN value set for variable: $variable"
		return -1
	fi
	return 0
}


function verify_mac_address(){
	variable=$1
	value=$2
	mac_address_pattern="^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
	if ! [[ $value =~ $mac_address_pattern ]]; then
		add_report $variable error "Incorrect MAC address value set for variable: $variable"
		return -1
	fi
	return 0
}

function detect_key_and_certificate_file_format() {
	file=$1
	is_pfx=`openssl pkcs12 -in "$file" -nokeys -passin pass:1 2>&1 | grep encoding -v | wc -l`
	if [[ $((is_pfx)) -eq 1 ]]; then
		echo "pfx"
		return 0
	fi
	is_der=`openssl x509 -inform der -in "$file" -passin pass:1 -noout 2>&1 | wc -l`
	if [[ $((is_der)) -eq 0 ]]; then
		echo "der"
		return 0
	fi
	is_pem=`openssl x509 -in "$file" -passin pass:1 -noout 2>&1 | wc -l`
	if [[ $((is_pem)) -eq 0 ]]; then
		echo "pem"
		return 0
	fi
	is_pkcs8_key=`openssl pkcs8 -in "$file" -topk8 -passout pass: -passin pass:1 2>&1 | grep BEGIN | wc -l`
	if [[ $((is_pkcs8_key)) -eq 1 ]]; then
		echo "pkcs8_key"
		return 0
	fi
	is_pkcs8_key_encrypted=`openssl pkcs8 -in "$file" -topk8 -passin pass:1 2>&1 | grep "wrong password" | wc -l`
	if [[ $((is_pkcs8_key_encrypted)) -eq 1 ]]; then
		echo "pkcs8_key_encrypted"
		return 0
	fi
	echo "unknown"
	return -1
}


function check_file_exists(){
	variable=$1
	value=$2
	file_occurences=`ls $value 2>/dev/null | wc -l `
	if [[ $((file_occurences)) -lt 1 ]]; then
		add_report $variable error "Read file error: $value for: $variable"
		return -1
	fi
}


function verify_certificate_and_private_key(){
	certificate_variable=$1
	certificate_file=$2

	#Check if certificate file exists
	file_occurences=`ls $certificate_file 2>/dev/null | wc -l `
	if [[ $((file_occurences)) -lt 1 ]]; then
		add_report $certificate_variable error "Read file error: $certificate_file for: $certificate_variable"
		return -1
	fi

	#Check if certificate format is supported
	certificate_file_format=$(detect_key_and_certificate_file_format $certificate_file)
	if [[ $certificate_file_format == "unknown" ]]; then
		add_report $certificate_variable error "Certificate format unknown. File: $certificate_file variable: $certificate_variable"
		return -1
	elif [[ $certificate_file_format == "" ]]; then
		add_report $certificate_variable error "Error while detecting certificate format! File: $certificate_file variable: $certificate_variable"
		return -1
	elif ! [[ 
			$certificate_file_format == "pfx" || 
			$certificate_file_format == "pem" || 
			$certificate_file_format == "der" ]]; then
				add_report $certificate_variable error "Certificate file error for $certificate_variable - $certificate_file format not supported"
				return -1
	fi

	#Read certificate password if needed
	is_cert_file_password_protected=`openssl x509 -in $certificate_file -noout -passin pass: 2>&1 | grep "empty password"`
	if ! [[ $is_cert_file_password_protected == "" ]]; then
		read -s -p "Please provide password for $certificate_file: " cert_password
		echo
	fi

	#Check certificate date
	cert_end_date=`openssl x509 -in $certificate_file -noout -enddate -passin pass:$cert_password | cut -d = -f 2`
	if ! [[ $cert_end_date == "" ]]; then
		cert_end_date_timestamp=$((`date -j -f "%b %d %H:%M:%S %Y %Z" "$cert_end_date" "+%s"`))
		current_timestamp=$((`date +%s`))
		if ! [[ $current_timestamp -lt $cert_end_date_timestamp ]]; then
			add_report $certificate_variable error "Certificate expired for: $certificate_variable file: $certificate_file"
			return -1
		fi
	fi

	#Check if CN match IUT_FQDN
	IUT_FQDN=`cat $CONFIG_FILE | grep "IUT_FQDN" -w | sed '/^#/d' | sed 's/.*=//' | sed "s/[\'\"]//g"`
	cert_CN=`openssl x509 -in $certificate_file -noout -text -passin pass:$cert_password | grep Subject | sed -n 's/^.*CN=\([^,]*\).*$/\1/p'`
	if ! [[ $cert_CN == $IUT_FQDN ]]; then
		add_report $certificate_variable error "Certificate CN $cert_CN does not match IUT_FQDN: $IUT_FQDN for $certificate_variable file: $certificate_file"
		return -1
	fi

	if [[ $certificate_file_format == "pfx" ]]; then
		return 0
	fi

	#Check if key file exists
	key_variable=`echo $certificate_variable | sed 's/CERT/KEY/'`
	key_file=`cat $CONFIG_FILE | sed '/^#/d' | grep $key_variable -w | sed 's/.*=//' | sed "s/[\'\"]//g"`
	if [[ $key_file == "" ]]; then
		add_report $key_variable error "Read value error for variable: $key_variable"
		return -1
	fi
	file_occurences=`ls $key_file 2>/dev/null | wc -l `
	if [[ $((file_occurences)) -lt 1 ]]; then
		add_report $key_variable error "Read file error: $key_file for: $key_variable"
		return -1
	fi

	#Check if key format is supported
	key_file_format=$(detect_key_and_certificate_file_format $key_file)
	if [[ $key_file_format == "unknown" ]]; then
		add_report $key_variable error "Private key format unknown. File: $key_file variable: $key_variable"
		return -1
	elif [[ $key_file_format == "" ]]; then
		add_report $key_variable error "Error while detecting certificate format! File: $key_file variable: $key_variable"
		return -1
	elif ! [[ $key_file_format == "pkcs8_key"* ]]; then
		add_report $key_variable error "Public key file error for $key_variable - $key_file format not supported"
		return -1
	fi

	#Read key file password if needed
	is_key_file_password_protected=`openssl rsa -check -in $key_file -noout -passin pass: 2>&1 | grep "empty password"`
	if ! [[ $is_key_file_password_protected == "" ]]; then
		read -s -p "Please provide password for $key_file: " key_password
		echo
	fi
	
	#Check if certificate and key files match
	certificate_file_md5=`openssl x509 -in $certificate_file -noout -modulus | openssl md5 | awk '{print $2}'`
	key_file_md5=`openssl rsa -in $key_file -noout -modulus -passin pass:$key_password | openssl md5 | awk '{print $2}'`
	if ! [[ $certificate_file_md5 == $key_file_md5 ]]; then
		add_report $certificate_variable error "Certificate and private key files do not match for $certificate_variable and $key_variable"
		return -1
	fi
	
	return 0
}


function check_value(){
	variable=$1
	value=`cat $CONFIG_FILE | sed '/^#/d' | grep $variable -w | sed 's/.*=//' | sed "s/[\'\"]//g"`
	if [[ $value == "" ]]; then
		add_report $variable "error" "Read value error for variable: $variable"
	fi
	if [[ $variable == *"IUT_TYPE"* ]]; then
		verify_iut_type $variable $value
	fi
	if [[ $variable == *"FQDN"* ]]; then
		verify_fqdn $variable $value
	fi
	if [[ $variable == "IF_"*"_NAME" ]]; then
		verify_if_name $variable $value
	fi
	if [[ $variable == *"IP_ADDRESS"* || $variable == *"SUBNET_MASK"* ]]; then
		verify_ip_address $variable $value
	fi
	if [[ $variable == *"MAC_ADDRESS"* ]]; then
		verify_mac_address $variable $value
	fi
	if [[ $variable == *"CERT" ]]; then
		verify_certificate_and_private_key $variable $value
	fi
}


function check_single_variables(){
	list_name=$1
	list=("${!list_name}")
	for variable in "${list[@]}"; do
		variable_from_file=`cat $CONFIG_FILE | sed '/^#/d' | grep $variable -w | cut -d '=' -f 1 | cut -d ':' -f 1 `
		occurences_in_file=`echo $variable_from_file | grep "$variable" -w -o | wc -l`
		if [[ $((occurences_in_file)) -gt 1 ]]; then
			add_report $variable warning "Duplicates found for variable: $variable"
		elif [[ $((occurences_in_file)) -eq 0 ]]; then
			add_report $variable error "Missing variable: $variable"
		else
			check_value $variable
		fi
	done
}


function check_group_variables(){
	list_name=$1
	list=("${!list_name}")
	prefix=`echo "${list[0]}" | sed 's/\[ID\]/\'$'\n/g' | awk 'NR==1 {print}'`
	groups=`cat $CONFIG_FILE | sed '/^#/d' | grep -oE "$prefix[0-9]+" | sed "s/^$prefix//" | sort -n | uniq`
	for group in $groups; do
		for variable_pattern in "${list[@]}"; do
			variable_name=`echo $variable_pattern | sed 's/\[ID\]/\'$'\n/g' | awk 'NR==2 {print}'`
			variable_from_file=`cat $CONFIG_FILE | grep "^$prefix$group$variable_name" -w -o | cut -d '=' -f 1 | cut -d ':' -f 1`
			variable=`echo $variable_from_file | awk '{print $1}'`
			occurences_in_file=`echo $variable_from_file | grep "$variable_from_file" -w -o | wc -l`
			if [[ $((occurences_in_file)) -gt 1 ]]; then
				add_report $variable warning "Duplicates found for variable: $variable"
			elif [[ $((occurences_in_file)) -eq 0 ]]; then
				variable=$prefix$group$variable_name
				add_report $variable error "Missing variable: $variable"
			else
				check_value $variable
			fi
		done
	done
}


function print_report_and_exit {
	if [[ $WARNINGS == "" ]] && [[ $ERRORS == "" ]]; then
		echo "Result: PASSED"
		exit 0
	fi
	echo "Result: FAILED"
	echo
	if ! [[ $WARNINGS == "" ]]; then
		for warning in "${WARNINGS[@]}"; do
			echo $warning
		done
	fi
	if ! [[ $ERRORS == "" ]]; then
		for error in "${ERRORS[@]}"; do
			echo $error
		done
	fi
	exit 1
}


echo "Verification of config file: '$CONFIG_FILE'... "

check_single_variables IUT_VARIABLES[@]
check_group_variables IF_VARIABLES[@]
print_report_and_exit

exit 0
