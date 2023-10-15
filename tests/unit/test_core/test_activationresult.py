from unittest.mock import Mock
from wakepy.core import ActivationResult, StageName
from wakepy.core.activationresult import (
    ModeSwitcher,
    MethodUsageResult,
    SuccessStatus,
)

switcher = Mock(spec_set=ModeSwitcher)


def test_activation_result():
    ar = ActivationResult(switcher)

    ar._results = [
        MethodUsageResult(
            status=SuccessStatus.FAIL,
            failure_stage=StageName.PLATFORM_SUPPORT,
            method_name="fail-platform",
            message="Platform XYZ not supported!",
        ),
        MethodUsageResult(
            status=SuccessStatus.FAIL,
            failure_stage=StageName.REQUIREMENTS,
            method_name="fail-requirements",
            message="Missing requirement: Some SW v.1.2.3",
        ),
        MethodUsageResult(
            status=SuccessStatus.SUCCESS,
            method_name="a-successful-method",
        ),
        MethodUsageResult(
            status=SuccessStatus.UNUSED,
            method_name="some-unused-method",
        ),
    ]

    assert ar.success
    assert ar.real_success
    assert not ar.failure

    assert ar.active_methods == ["a-successful-method"]
    assert ar.active_methods_string == "a-successful-method"


def test_activation_result_three_successful():
    ar = ActivationResult(switcher)

    ar._results = [
        MethodUsageResult(
            status=SuccessStatus.SUCCESS,
            method_name="1st.successfull.method",
        ),
        MethodUsageResult(
            status=SuccessStatus.FAIL,
            failure_stage=StageName.REQUIREMENTS,
            method_name="fail-requirements",
            message="Missing requirement: Some SW v.1.2.3",
        ),
        MethodUsageResult(
            status=SuccessStatus.SUCCESS,
            method_name="2nd-successful-method",
        ),
        MethodUsageResult(
            status=SuccessStatus.SUCCESS,
            method_name="last-successful-method",
        ),
    ]

    assert ar.success
    assert ar.real_success
    assert not ar.failure

    assert ar.active_methods == [
        "1st.successfull.method",
        "2nd-successful-method",
        "last-successful-method",
    ]
    assert (
        ar.active_methods_string
        == "1st.successfull.method, 2nd-successful-method & last-successful-method"
    )
