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

RESULTS_3_FAIL = [
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


@pytest.mark.parametrize(
    "results, success, real_success, failure, faking_success",
    [
        (RESULTS_1, True, True, False, "0"),
        (RESULTS_2, True, True, False, "0"),
        (RESULTS_3_FAIL, False, False, True, "0"),
        (RESULTS_3_FAIL, False, False, True, "1"),
    ],
)
def test_activation_result_success(
    results, success, real_success, failure, faking_success
):
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("WAKEPY_FAKE_SUCCESS", str(faking_success))
    ar = ActivationResult(switcher)
    ar._results = results

    assert ar.success == success
    assert ar.real_success == real_success
    assert ar.failure == failure


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


@pytest.mark.parametrize(
    "status, failure_stage, method_name, message, expected_string_representation",
    [
        (
            UsageStatus.FAIL,
            StageName.PLATFORM_SUPPORT,
            "fail-platform",
            "Platform XYZ not supported!",
            '(FAIL @PLATFORM_SUPPORT, fail-platform, "Platform XYZ not supported!")',
        ),
        (
            UsageStatus.FAIL,
            StageName.REQUIREMENTS,
            "other-fail-method",
            "Need SW X version >= 8.9!",
            '(FAIL @REQUIREMENTS, other-fail-method, "Need SW X version >= 8.9!")',
        ),
        (
            UsageStatus.SUCCESS,
            None,
            "successfulMethod",
            "",
            # Succesful methods do not print empty message
            "(SUCCESS, successfulMethod)",
        ),
        (
            UsageStatus.UNUSED,
            None,
            "SomeMethod",
            "",
            # Unused methods do not print empty message
            "(UNUSED, SomeMethod)",
        ),
    ],
)
def test_method_usage_result(
    status,
    failure_stage,
    method_name,
    message,
    expected_string_representation,
):
    mur = MethodUsageResult(
        status=status,
        failure_stage=failure_stage,
        method_name=method_name,
        message=message,
    )
    # These attributes are available
    assert mur.status == status
    assert mur.failure_stage == failure_stage
    assert mur.method_name == method_name
    assert mur.message == message

    assert str(mur) == expected_string_representation


def test_stagename():
    assert StageName.PLATFORM_SUPPORT == "PLATFORM_SUPPORT"
    assert StageName.ACTIVATION == "ACTIVATION"
    assert StageName.REQUIREMENTS == "REQUIREMENTS"


def test_usagestatus():
    assert UsageStatus.FAIL == "FAIL"
    assert UsageStatus.SUCCESS == "SUCCESS"
    assert UsageStatus.UNUSED == "UNUSED"
