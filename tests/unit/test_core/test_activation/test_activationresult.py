import re
import pytest

from wakepy.core import ActivationResult, MethodActivationResult
from wakepy.core.activation import StageName

PLATFORM_SUPPORT_FAIL = MethodActivationResult(
    success=False,
    failure_stage=StageName.PLATFORM_SUPPORT,
    method_name="fail-platform",
    failure_reason="Platform XYZ not supported!",
)
REQUIREMENTS_FAIL = MethodActivationResult(
    success=False,
    failure_stage=StageName.REQUIREMENTS,
    method_name="fail-requirements",
    failure_reason="Missing requirement: Some SW v.1.2.3",
)
SUCCESS_RESULT = MethodActivationResult(
    success=True,
    method_name="a-successful-method",
)
UNUSED_RESULT = MethodActivationResult(
    success=None,
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
        success=True,
        method_name="1st.successfull.method",
    ),
    REQUIREMENTS_FAIL,
    MethodActivationResult(
        success=True,
        method_name="2nd-successful-method",
    ),
    MethodActivationResult(
        success=True,
        method_name="last-successful-method",
    ),
]

METHODACTIVATIONRESULTS_3_FAIL = [
    MethodActivationResult(
        success=False,
        failure_stage=StageName.PLATFORM_SUPPORT,
        method_name="fail-platform",
        failure_reason="Platform XYZ not supported!",
    ),
    MethodActivationResult(
        success=False,
        failure_stage=StageName.REQUIREMENTS,
        method_name="fail-requirements",
        failure_reason="Missing requirement: Some SW v.1.2.3",
    ),
]


def test_activation_result_list_methods():
    ar = ActivationResult()
    ar._results = [
        PLATFORM_SUPPORT_FAIL,
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
        UNUSED_RESULT,
    ]

    # By default, the list_methods drops out failures occuring in the
    # platform stage
    assert ar.list_methods() == [
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
        UNUSED_RESULT,
    ]

    # The same as above but with explicit arguments.
    assert ar.list_methods(ignore_platform_fails=True) == [
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
        UNUSED_RESULT,
    ]

    # Do not ignore platform fails
    assert ar.list_methods(ignore_platform_fails=False) == [
        PLATFORM_SUPPORT_FAIL,
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
        UNUSED_RESULT,
    ]

    # ignore unused
    assert ar.list_methods(ignore_platform_fails=False, ignore_unused=True) == [
        PLATFORM_SUPPORT_FAIL,
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
    ]


def test_activation_result_query():
    ar = ActivationResult()
    ar._results = [
        PLATFORM_SUPPORT_FAIL,
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
        UNUSED_RESULT,
    ]

    # When no arguments given, return everything
    assert ar.query() == [
        PLATFORM_SUPPORT_FAIL,
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
        UNUSED_RESULT,
    ]

    # Possible to filter with status
    assert ar.query(success=(False,)) == [
        PLATFORM_SUPPORT_FAIL,
        REQUIREMENTS_FAIL,
    ]

    # Possible to filter with fail_stage
    assert ar.query(fail_stages=("REQUIREMENTS",)) == [
        REQUIREMENTS_FAIL,
        SUCCESS_RESULT,
        UNUSED_RESULT,
    ]

    # or with both
    assert ar.query(success=(False,), fail_stages=("REQUIREMENTS",)) == [
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


def test_active_method():
    ar = ActivationResult(METHODACTIVATIONRESULTS_1)
    assert ar.active_method == "a-successful-method"


def test_active_method_with_fails():
    ar = ActivationResult([PLATFORM_SUPPORT_FAIL, REQUIREMENTS_FAIL])
    assert ar.active_method is None


def test_active_method_with_multiple_success():
    ar = ActivationResult(METHODACTIVATIONRESULTS_2)
    with pytest.raises(
        ValueError,
        match=re.escape(
            "The ActivationResult cannot have more than one active methods! Active methods: ['1st.successfull.method', '2nd-successful-method', 'last-successful-method']"
        ),
    ):
        ar.active_method
