import os
from unittest.mock import Mock

import pytest

from wakepy.core import ActivationResult
from wakepy.core.activationresult import (
    MethodUsageResult,
    ModeSwitcher,
    StageName,
    UsageStatus,
    should_fake_success,
)

switcher = Mock(spec_set=ModeSwitcher)

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
RESULTS_1 = [
    PLATFORM_SUPPORT_FAIL,
    REQUIREMENTS_FAIL,
    SUCCESS_RESULT,
    UNUSED_RESULT,
]

RESULTS_2 = [
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
    "results, success_expected, real_success_expected, faking_success",
    [
        (RESULTS_1, True, True, "0"),
        (RESULTS_2, True, True, "0"),
        (RESULTS_3_FAIL, False, False, "0"),
        (RESULTS_3_FAIL, True, False, "1"),
    ],
)
def test_activation_result_success(
    results, success_expected, real_success_expected, faking_success
):
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("WAKEPY_FAKE_SUCCESS", str(faking_success))
        ar = ActivationResult(switcher)
        ar._results = results

        assert ar.success == success_expected
        assert ar.real_success == real_success_expected
        assert ar.failure == (not success_expected)


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


def test_activation_result_get_details():
    ar = ActivationResult(switcher)
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
    ar = ActivationResult(switcher)
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


def test_should_fake_success(monkeypatch):
    for val in ("1", "yes", "True", "anystring"):
        with monkeypatch.context() as mp:
            mp.setenv("WAKEPY_FAKE_SUCCESS", val)
            val_from_env = os.environ.get("WAKEPY_FAKE_SUCCESS")
            assert val_from_env == str(val)
            assert should_fake_success() is True
    for val in ("0", "no", "NO", "False", "false", "FALSE"):
        with monkeypatch.context() as mp:
            mp.setenv("WAKEPY_FAKE_SUCCESS", val)
            val_from_env = os.environ.get("WAKEPY_FAKE_SUCCESS")
            assert val_from_env == str(val)
            assert should_fake_success() is False
