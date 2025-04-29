import yaml


def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def main():
    data = load_yaml("LOG_007/test_config.yaml")  # Replace with your YAML file path

    # Example: print the first `http_url` if it exists
    try:
        for i in range(0, 52):
            name = data["test_config"]["conformance"]["tests"][0]["variations"][i]['name']
            print(f'"{name}",')
    except (KeyError, IndexError, TypeError) as e:
        print(f"Could not extract http_url: {e}")

    # Keep `data` for later use if needed
    return data


if __name__ == "__main__":
    full_data = main()

