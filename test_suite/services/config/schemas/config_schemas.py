TEST_CONFIG_SCHEMA = {
    "test_config": {
        "required": True,
        "type": dict,
        "schema": {
            "conformance": {
                "required": True,
                "type": dict,
                "schema": {
                    "tests": {
                        "required": True,
                        "type": list,
                        "schema": {
                            "name": {
                                "required": True,
                                "type": str
                            },
                            "variations": {
                                "required": True,
                                "type": list,
                                "schema": {
                                    "name": {"required": True, "type": str},
                                    "description": {"required": False, "type": str},
                                    "params": {
                                        "required": True,
                                        "type": dict,
                                        "schema": {
                                            "messages": {
                                                "required": True,
                                                "type": list,
                                                "schema": {
                                                    "action": {
                                                        "required": True,
                                                        "type": str,
                                                        "allowed": ["receive", "send", "command", "manual"]
                                                    },
                                                    "id": {
                                                        "required": False, "type": str
                                                    },
                                                    "preparation_steps": {
                                                        "required": False,
                                                        "type": dict,
                                                        "schema": {
                                                            "method_name": {"required": False, "type": str},
                                                            "kwargs": {"required": False, "type": dict},
                                                            "save_result_as": {
                                                                "required": False,
                                                                "type": list,
                                                            }
                                                        }
                                                    },
                                                    "type": {
                                                        "required": True,
                                                        "type": str,
                                                        "allowed": ["SIP", "HTTP", ""]
                                                    },
                                                    "method": {
                                                        "required": True,
                                                        "type": str,
                                                        "allowed": ["INVITE", "MESSAGE", "ACK", "BYE", "CANCEL",
                                                                    "REGISTER", "OPTIONS", "PRACK", "SUBSCRIBE",
                                                                    "NOTIFY", "PUBLISH", "INFO", "REFER", "UPDATE",
                                                                    "GET", "HEAD", "PUT", "POST", "DELETE", "OPTIONS",
                                                                    "TRACE", "CONNECT", "PATCH", ""
                                                                    ]
                                                    },
                                                    "response_code": {"required": False, "type": str},
                                                    "http_url": {"required": False, "type": str},
                                                    "body": {"required": False, "type": str},
                                                    "sipp_scenario": {
                                                        "required": False,
                                                        "type": dict,
                                                        "schema": {
                                                            "scenario_file_path": {"required": False, "type": str},
                                                            "kwargs": {"required": False, "type": dict},
                                                            "save_response_as": {"required": False, "type": str},
                                                            "save_log_as": {"required": False, "type": str},
                                                        }
                                                    },
                                                    "run_in_background": {
                                                        "required": False,
                                                        "type": str,
                                                        "allowed": ["True", "False"]
                                                    },

                                                }
                                            },
                                        }
                                    }
                                }
                            },
                            "requirements": {
                                "required": True,
                                "type": list,
                                "schema": {
                                    "name": {"required": True, "type": str},
                                    "variations": {
                                        "required": True,
                                        "type": list
                                    }
                                }
                            },
                        }
                    },
                },
            },
        }
    }

}

RUN_CONFIG_SCHEMA = {
    "run_config": {
        "required": True,
        "type": dict,
        "schema": {
            "global": {
                "required": True,
                "type": dict,
                "schema": {
                    "response_timeout": {"required": True, "type": int},
                    "type": {"required": True, "type": str},
                    "report_files": {
                        "required": True,
                        "type": list,
                        "schema": {
                            "type": {"required": True, "type": str},
                            "path": {"required": True, "type": str},  # Add file existence check if needed
                        },
                    },
                    "log": {
                        "required": True,
                        "type": dict,
                        "schema": {
                            "level": {"required": True, "type": str},
                            "output_file": {"required": True, "type": str},
                        },
                    },
                },
            },
            "tests": {
                "required": False,
                "type": list,  # <-- Changed from dict to list
                "schema": {  # This describes each element of the list
                    "name": {"required": True, "type": str},
                    "requirements": {
                        "required": True,
                        "type": list,
                        "schema": {
                            "name": {"required": True, "type": str},
                            "variations": {"required": True, "type": list},  # list of strings
                        },
                    },
                    "variations": {
                        "required": True,
                        "type": list,
                        "schema": {
                            "name": {"required": True, "type": str},
                            "mode": {"required": True, "type": str, "allowed": ["pcap", "online"]},
                            "pcap_file": {"required": False, "type": str},  # optional
                            "params": {
                                "required": False,  # params optional
                                "type": dict,
                                "schema": {
                                    "messages": {
                                        "required": True,
                                        "type": list,
                                        "schema": {
                                            "action": {
                                                "required": True,
                                                "type": str,
                                                "allowed": ["receive", "send", "command", "manual"]
                                            },
                                            "id": {
                                                "required": False, "type": str
                                            },
                                            "preparation_steps": {
                                                "required": False,
                                                "type": dict,
                                                "schema": {
                                                    "method_name": {"required": False, "type": str},
                                                    "kwargs": {"required": False, "type": dict},
                                                    "save_result_as": {
                                                        "required": False,
                                                        "type": list,
                                                    }
                                                }
                                            },
                                            "type": {
                                                "required": True,
                                                "type": str,
                                                "allowed": ["SIP", "HTTP", ""]
                                            },
                                            "method": {
                                                "required": True,
                                                "type": str,
                                                "allowed": [
                                                    "INVITE", "MESSAGE", "ACK", "BYE", "CANCEL",
                                                    "REGISTER", "OPTIONS", "PRACK", "SUBSCRIBE",
                                                    "NOTIFY", "PUBLISH", "INFO", "REFER", "UPDATE",
                                                    "GET", "HEAD", "PUT", "POST", "DELETE", "OPTIONS",
                                                    "TRACE", "CONNECT", "PATCH", ""]
                                            },
                                            "response_code": {"required": False, "type": str},
                                            "http_url": {"required": False, "type": str},
                                            "body": {"required": False, "type": str},
                                            "sipp_scenario": {
                                                "required": False,
                                                "type": dict,
                                                "schema": {
                                                    "scenario_file_path": {"required": False, "type": str},
                                                    "kwargs": {"required": False, "type": dict},
                                                    "save_response_as": {"required": False, "type": str},
                                                    "save_log_as": {"required": False, "type": str},
                                                }
                                            },
                                            "run_in_background": {
                                                "required": False,
                                                "type": str,
                                                "allowed": ["True", "False"]
                                            },

                                        }
                                    }
                                },
                            },
                            "filtering_options": {
                                "required": False,  # filtering_options optional
                                "type": list,
                                "schema": {
                                    "message_type": {
                                        "required": True,
                                        "type": str,
                                        "allowed": ["stimulus", "output", "other"]
                                    },
                                    "src_interface": {"required": False, "type": str},
                                    "dst_interface": {"required": False, "type": str},
                                    "sip_method": {"required": False, "type": str},
                                    "http_request_method": {"required": False, "type": str},
                                    "response_status_code": {"required": False, "type": str},
                                    "body_contains": {"required": False, "type": str},
                                    "header_contains": {"required": False, "type": str},
                                },
                            },
                        },
                    },
                },
            },
        }
    }
}

LAB_CONFIG_SCHEMA = {
    "lab_config": {
        "required": True,
        "type": dict,
        "schema": {
            "pca_certificate_file": {"required": False, "type": str},
            "pca_certificate_key": {"required": False, "type": str},
            "test_suite_host_ip": {"required": True, "type": str},
            "entities": {
                "required": True,
                "type": list,
                "schema": {
                    "name": {"required": True, "type": str},
                    "mode": {
                        "required": True,
                        "type": str,
                        "allowed": ["REAL_DEVICE", "STUB_SERVER"]
                    },
                    "role": {
                        "required": True,
                        "type": str,
                        "allowed": ["SENDER", "RECEIVER", "IUT", "OTHER"]
                    },
                    "function": {
                        "required": True,
                        "type": str,
                        "allowed": ["OSP", "BCF", "ESRP", "ECRF-LVF", "PS", "LOG", "CHE", "BRIDGE", "LIS", "ADR"]
                    },
                    "fqdn": {"required": False, "type": str, "nullable": True},
                    "certificate_file": {"required": True, "type": str},
                    "certificate_key": {"required": True, "type": str},
                    "interfaces": {
                        "required": True,
                        "type": list,
                        "schema": {
                            "name": {"required": True, "type": str},
                            "fqdn": {"required": False, "type": str, "nullable": True},
                            "ip": {"required": True, "type": str},
                            "mask": {"required": False, "type": str, "nullable": True},
                            "gateway": {"required": False, "type": str, "nullable": True},
                            "dns": {
                                "required": False,
                                "type": list,
                                "schema": {"type": str},
                                "nullable": True
                            },
                            "port_mapping": {
                                "required": True,
                                "type": list,
                                "schema": {
                                    "protocol": {"required": True, "type": str, "allowed": ["TLSv1.3", "HTTP", "SIP"]},
                                    "port": {"required": True, "type": int, "min": 1, "max": 65535},
                                    "transport_protocol": {"required": True, "type": str, "allowed": [
                                        "TLSv1.3", "TLSv1.2", "mTLSv1.3", "mTLSv1.2", "TCP", "UDP"
                                    ]}
                                }
                            },
                        }
                    },
                }
            },
        }
    }
}

BASE_CONFIG_SCHEMA = {
    "test_config": {
        "required": True,
        "type": str,
        "nested_yaml": True,
        "schema": TEST_CONFIG_SCHEMA
    },
    "lab_config": {
        "required": True,
        "type": str,
        "nested_yaml": True,
        "schema": LAB_CONFIG_SCHEMA
    },
    "run_config": {
        "required": False,
        "type": str,
        "nested_yaml": True,
        "schema": RUN_CONFIG_SCHEMA
    },

}
