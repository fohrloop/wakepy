from unittest.mock import Mock

import pytest

from wakepy.core import ActivationResult, MethodUsageResult
from wakepy.core.activation import StageName, UsageStatus
from wakepy.core.activationmanager import ModeActivationManager

mockmanager = Mock(spec_set=ModeActivationManager)

PLATFORM_SUPPORT_FAIL = MethodUsageResult(
    status=UsageStatus.FAIL,
    failure_stage=StageName.PLATFORM_SUPPORT,
    method_name="fail-platform",
    message="Platform XYZ not supported!",
)
REQUIREMENTS_FAIL = MethodUsageResult(
    status=UsageStatus.FAIL,
    failure_stage=StageName.REQUIREMENTS,
    method_name="fail-requirements",
    message="Missing requirement: Some SW v.1.2.3",
)
SUCCESS_RESULT = MethodUsageResult(
    status=UsageStatus.SUCCESS,
    method_name="a-successful-method",
)
UNUSED_RESULT = MethodUsageResult(
    status=UsageStatus.UNUSED,
    method_name="some-unused-method",
)
METHODUSAGERESULTS_1 = [
    PLATFORM_SUPPORT_FAIL,
    REQUIREMENTS_FAIL,
    SUCCESS_RESULT,
    UNUSED_RESULT,
]

METHODUSAGERESULTS_2 = [
    MethodUsageResult(
        status=UsageStatus.SUCCESS,
        method_name="1st.successfull.method",
    ),
    REQUIREMENTS_FAIL,
    MethodUsageResult(
        status=UsageStatus.SUCCESS,
        method_name="2nd-successful-method",
    ),
    MethodUsageResult(
        status=UsageStatus.SUCCESS,
        method_name="last-successful-method",
    ),
]

METHODUSAGERESULTS_3_FAIL = [
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
]


def test_activation_result_get_details():
    ar = ActivationResult(mockmanager)
    ar._results = [
        PLATFORM_SUPPORT_FAIL,
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
        UNUSED_RESULT,
    ]

    # By default, the get_details drops out failures occuring in the
    # platform stage
    assert ar.get_details() == [
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
        UNUSED_RESULT,
    ]

    # The same as above but with explicit arguments.
    assert ar.get_details(ignore_platform_fails=True) == [
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
        UNUSED_RESULT,
    ]

    # Do not ignore platform fails
    assert ar.get_details(ignore_platform_fails=False) == [
        PLATFORM_SUPPORT_FAIL,
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
        UNUSED_RESULT,
    ]

    # ignore unused
    assert ar.get_details(ignore_platform_fails=False, ignore_unused=True) == [
        PLATFORM_SUPPORT_FAIL,
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
    ]


def test_activation_result_get_detailed_results():
    ar = ActivationResult(mockmanager)
    ar._results = [
        PLATFORM_SUPPORT_FAIL,
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
        UNUSED_RESULT,
    ]

    # When no arguments given, return everything
    assert ar.get_detailed_results() == [
        PLATFORM_SUPPORT_FAIL,
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
        UNUSED_RESULT,
    ]

    # Possible to filter with status
    assert ar.get_detailed_results(statuses=("FAIL",)) == [
        PLATFORM_SUPPORT_FAIL,
        REQUIREMENTS_FAIL,
    ]

    # Possible to filter with fail_stage
    assert ar.get_detailed_results(fail_stages=("REQUIREMENTS",)) == [
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
        UNUSED_RESULT,
    ]

    # or with both
    assert ar.get_detailed_results(
        statuses=("FAIL",), fail_stages=("REQUIREMENTS",)
    ) == [
        REQUIREMENTS_FAIL,
    ]


@pytest.mark.parametrize(
    "results, success_expected, real_success_expected, faking_success",
    [
        (METHODUSAGERESULTS_1, True, True, "0"),
        (METHODUSAGERESULTS_2, True, True, "0"),
        (METHODUSAGERESULTS_3_FAIL, False, False, "0"),
        (METHODUSAGERESULTS_3_FAIL, True, False, "1"),
    ],
)
def test_activation_result_success(
    results, success_expected, real_success_expected, faking_success
):
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("WAKEPY_FAKE_SUCCESS", str(faking_success))
        ar = ActivationResult(mockmanager)
        ar._results = results

        assert ar.success == success_expected
        assert ar.real_success == real_success_expected
        assert ar.failure == (not success_expected)


@pytest.mark.parametrize(
    "results, expected_active_methods, expected_active_methods_string",
    [
        (METHODUSAGERESULTS_1, ["a-successful-method"], "a-successful-method"),
        (
            METHODUSAGERESULTS_2,
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
    ar = ActivationResult(mockmanager)
    ar._results = results

    assert ar.active_methods == expected_active_methods
    assert ar.active_methods_string == expected_active_methods_string
