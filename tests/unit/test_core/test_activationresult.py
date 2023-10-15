from unittest.mock import Mock
from wakepy.core import ActivationResult, StageName
from wakepy.core.activationresult import (
    ModeSwitcher,
    MethodUsageResult,
    UsageStatus,
)

import pytest

switcher = Mock(spec_set=ModeSwitcher)

RESULTS_1 = [
    MethodUsageResult(
        status=UsageStatus.FAIL,
        failure_stage=StageName.PLATFORM_SUPPORT,
        method_name="fail-platform",
        message="Platform XYZ not supported!",
    ),
    MethodUsageResult(
        status=UsageStatus.FAIL,
        failure_stage=StageName.REQUIREMENTS,
        method_name="fail-requirements",
        message="Missing requirement: Some SW v.1.2.3",
    ),
    MethodUsageResult(
        status=UsageStatus.SUCCESS,
        method_name="a-successful-method",
    ),
    MethodUsageResult(
        status=UsageStatus.UNUSED,
        method_name="some-unused-method",
    ),
]

RESULTS_2 = [
    MethodUsageResult(
        status=UsageStatus.SUCCESS,
        method_name="1st.successfull.method",
    ),
    MethodUsageResult(
        status=UsageStatus.FAIL,
        failure_stage=StageName.REQUIREMENTS,
        method_name="fail-requirements",
        message="Missing requirement: Some SW v.1.2.3",
    ),
    MethodUsageResult(
        status=UsageStatus.SUCCESS,
        method_name="2nd-successful-method",
    ),
    MethodUsageResult(
        status=UsageStatus.SUCCESS,
        method_name="last-successful-method",
    ),
]


@pytest.mark.parametrize(
    "results, expected_success, expected_failure",
    [
        (RESULTS_1, True, False),
        (RESULTS_2, True, False),
    ],
)
def test_activation_result_success(results, expected_success, expected_failure):
    ar = ActivationResult(switcher)
    ar._results = results

    assert ar.success == expected_success
    assert ar.real_success == expected_success
    assert ar.failure == expected_failure


@pytest.mark.parametrize(
    "results, expected_active_methods, expected_active_methods_string",
    [
        (RESULTS_1, ["a-successful-method"], "a-successful-method"),
        (
            RESULTS_2,
            [
                "1st.successfull.method",
                "2nd-successful-method",
                "last-successful-method",
            ],
            "1st.successfull.method, 2nd-successful-method & last-successful-method",
        ),
    ],
)
def test_active_methods(
    results, expected_active_methods, expected_active_methods_string
):
    ar = ActivationResult(switcher)
    ar._results = results

    assert ar.active_methods == expected_active_methods
    assert ar.active_methods_string == expected_active_methods_string
