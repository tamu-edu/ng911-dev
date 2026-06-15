import os
import sys
from parser import get_command_parser

sys.path.append(os.path.abspath("test_suite"))
sys.path.append(os.path.abspath("proxy_server"))

from shutdown import graceful_shutdown
from test_suite.api import (
    validate_configs,
    generate_report,
    run,
    generate_jws,
    decode_jws,
)
from test_suite.api_utils import (
    get_last_commit_hash,
    get_last_commit_details,
    running_as_root,
)
from proxy_server.api import run_management_server


def main():
    _parser = get_command_parser()
    args = _parser.parse_args()

    print(
        f"Launching Test Suite based on {get_last_commit_hash()} commit. Details: {get_last_commit_details()}"
    )

    if not running_as_root():
        print("⚠️ Test Suite have to be run as a root. ⚠️ Exiting...")
        return

    # Dispatch to the appropriate function
    if args.command == "validate":
        validate_configs(
            args.run_config,
            args.lab_config,
            args.lab_info,
            args.test_config,
            args.test_info,
            args.launch_config,
        )
    elif args.command == "gen_report":
        generate_report(
            args.json_file, args.report_type, args.filename, args.folder, args.detailed
        )
    elif args.command == "run":
        run(args.launch, args.use_rc, args.gen_rc)
    elif args.command == "generate_jws":
        print(
            generate_jws(
                json_source=args.json_file_path,
                cert_path=args.cert,
                key_path=args.key,
                key_password=args.password,
                output_file=args.output_file,
                cert_url=args.cert_url,
                disable_cert_url_checks=args.disable_cert_url_checks,
            )
        )
    elif args.command == "decode_jws":
        print(decode_jws(args.jws_file_path, args.key, args.password))
    elif args.command == "ms":
        run_management_server(host=args.host, port=int(args.port))
    else:
        _parser.print_help()


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        graceful_shutdown("KeyboardInterrupt (Ctrl+C)")

    except Exception as e:
        graceful_shutdown("Unhandled exception", e)
