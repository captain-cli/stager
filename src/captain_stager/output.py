import json


def emit_json(value):
    print(json.dumps(value, indent=2))


def print_report(report):
    print(f"Manifest: {report['manifestId']}")
    print(f"Root:     {report['root']}")
    print(f"Dry run:  {'yes' if report['dryRun'] else 'no'}")
    print()

    for operation in report['operations']:
        print(
            f"{operation['status'].upper().ljust(7)} "
            f"{operation['kind'].ljust(5)} "
            f"{operation['relativePath']}"
        )
        if operation.get('message'):
            print(f"        {operation['message']}")

    print()
    print(f"Result: {'success' if report['succeeded'] else 'failed'}")
