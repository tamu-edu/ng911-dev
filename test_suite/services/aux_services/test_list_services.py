from collections import defaultdict

from services.aux_services.aux_services import get_test_id_from_req


def optimize_test_list_for_variation(test_list: list) -> list:
    """
    Removes duplicates in test_list by test_id and merge subtests.
    :param test_list:
    :return: list
    """
    result = defaultdict(set)
    use_all_subtests = set()

    for test in test_list:
        test_id = test["test_id"]
        subtests = test["subtests"]

        if not subtests:
            # Indicates using all subtests, so clear and mark this test_id accordingly
            use_all_subtests.add(test_id)
            result[test_id] = set()  # Empty set as indicator
            continue

        # If test_id already marked as using all subtests, skip merging
        if test_id in use_all_subtests:
            continue

        result[test_id].update(subtests)

    # Convert sets back to sorted lists
    return [
        {"test_id": test_id, "subtests": [] if test_id in use_all_subtests else sorted(subtests)}
        for test_id, subtests in result.items()
    ]


def generate_test_list_for_variation(reqs: list, variation: str) -> list:
    result = []
    for req in reqs:
        normalized_variations = [v.lower() for v in req.variations]
        if variation.lower() in normalized_variations or "all" in normalized_variations:
            test_data = get_test_id_from_req(req.name)
            if test_data:
                test_id, subtests = test_data
                result.append({"test_id": test_id, "subtests": subtests})
    return optimize_test_list_for_variation(result)


