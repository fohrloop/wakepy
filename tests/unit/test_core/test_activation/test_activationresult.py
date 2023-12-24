import pytest

from wakepy.core import ActivationResult, MethodActivationResult
from wakepy.core.activation import StageName, UsageStatus

PLATFORM_SUPPORT_FAIL = MethodActivationResult(
    status=UsageStatus.FAIL,
    failure_stage=StageName.PLATFORM_SUPPORT,
    method_name="fail-platform",
    message="Platform XYZ not supported!",
)
REQUIREMENTS_FAIL = MethodActivationResult(
    status=UsageStatus.FAIL,
    failure_stage=StageName.REQUIREMENTS,
    method_name="fail-requirements",
    message="Missing requirement: Some SW v.1.2.3",
)
SUCCESS_RESULT = MethodActivationResult(
    status=UsageStatus.SUCCESS,
    method_name="a-successful-method",
)
UNUSED_RESULT = MethodActivationResult(
    status=UsageStatus.UNUSED,
    method_name="some-unused-method",
)
METHODACTIVATIONRESULTS_1 = [
    PLATFORM_SUPPORT_FAIL,
    REQUIREMENTS_FAIL,
    SUCCESS_RESULT,
    UNUSED_RESULT,
]

METHODACTIVATIONRESULTS_2 = [
    MethodActivationResult(
        status=UsageStatus.SUCCESS,
        method_name="1st.successfull.method",
    ),
    REQUIREMENTS_FAIL,
    MethodActivationResult(
        status=UsageStatus.SUCCESS,
        method_name="2nd-successful-method",
    ),
    MethodActivationResult(
        status=UsageStatus.SUCCESS,
        method_name="last-successful-method",
    ),
]

METHODACTIVATIONRESULTS_3_FAIL = [
    MethodActivationResult(
        status=UsageStatus.FAIL,
        failure_stage=StageName.PLATFORM_SUPPORT,
        method_name="fail-platform",
        message="Platform XYZ not supported!",
    ),
    MethodActivationResult(
        status=UsageStatus.FAIL,
        failure_stage=StageName.REQUIREMENTS,
        method_name="fail-requirements",
        message="Missing requirement: Some SW v.1.2.3",
    ),
]


def test_activation_result_get_details():
    ar = ActivationResult()
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
    ar = ActivationResult()
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
        (METHODACTIVATIONRESULTS_1, True, True, "0"),
        (METHODACTIVATIONRESULTS_2, True, True, "0"),
        (METHODACTIVATIONRESULTS_3_FAIL, False, False, "0"),
        (METHODACTIVATIONRESULTS_3_FAIL, True, False, "1"),
    ],
)
def test_activation_result_success(
    results, success_expected, real_success_expected, faking_success
):
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("WAKEPY_FAKE_SUCCESS", str(faking_success))
        ar = ActivationResult()
        ar._results = results

        assert ar.success == success_expected
        assert ar.real_success == real_success_expected
        assert ar.failure == (not success_expected)


@pytest.mark.parametrize(
    "results, expected_active_methods, expected_active_methods_string",
    [
        (METHODACTIVATIONRESULTS_1, ["a-successful-method"], "a-successful-method"),
        (
            METHODACTIVATIONRESULTS_2,
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
    ar = ActivationResult()
    ar._results = results

    assert ar.active_methods == expected_active_methods
    assert ar.active_methods_string == expected_active_methods_string
