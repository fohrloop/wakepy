from __future__ import annotations

import re
import typing

import pytest

from wakepy.core import ActivationResult, MethodActivationResult
from wakepy.core.activation import StageName, WakepyFakeSuccess

if typing.TYPE_CHECKING:
    from typing import List


@pytest.fixture
def mr_platform_support_fail() -> MethodActivationResult:
    return MethodActivationResult(
        success=False,
        failure_stage=StageName.PLATFORM_SUPPORT,
        method_name="fail-platform",
        failure_reason="Platform XYZ not supported!",
    )


@pytest.fixture
def mr_requirements_fail() -> MethodActivationResult:
    return MethodActivationResult(
        success=False,
        failure_stage=StageName.REQUIREMENTS,
        method_name="fail-requirements",
        failure_reason="Missing requirement: Some SW v.1.2.3",
    )


@pytest.fixture
def mr_success_result() -> MethodActivationResult:
    return MethodActivationResult(
        success=True,
        method_name="a-successful-method",
    )


@pytest.fixture
def mr_unused_result() -> MethodActivationResult:
    return MethodActivationResult(
        success=None,
        method_name="some-unused-method",
    )


@pytest.fixture
def mr_wakepy_fake_notinuse() -> MethodActivationResult:
    return MethodActivationResult(
        success=False,
        failure_stage=StageName.ACTIVATION,
        method_name=WakepyFakeSuccess.name,
    )


@pytest.fixture
def mr_wakepy_fake_success() -> MethodActivationResult:
    return MethodActivationResult(
        success=True,
        failure_stage=StageName.ACTIVATION,
        method_name=WakepyFakeSuccess.name,
    )


@pytest.fixture
def method_activation_results1(
    mr_platform_support_fail: MethodActivationResult,
    mr_requirements_fail: MethodActivationResult,
    mr_success_result: MethodActivationResult,
    mr_unused_result: MethodActivationResult,
) -> List[MethodActivationResult]:
    return [
        mr_platform_support_fail,
        mr_requirements_fail,
        mr_success_result,
        mr_unused_result,
    ]


@pytest.fixture
def method_activation_results2(
    mr_requirements_fail: MethodActivationResult,
) -> List[MethodActivationResult]:
    return [
        MethodActivationResult(
            success=True,
            method_name="1st.successful.method",
        ),
        # Fails in Requirement stage
        mr_requirements_fail,
        MethodActivationResult(
            success=True,
            method_name="2nd-successful-method",
        ),
        MethodActivationResult(
            success=True,
            method_name="last-successful-method",
        ),
    ]


@pytest.fixture
def method_activation_results3_fail() -> List[MethodActivationResult]:
    return [
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


@pytest.fixture
def method_activation_results4a(
    method_activation_results3_fail: List[MethodActivationResult],
    mr_wakepy_fake_notinuse: MethodActivationResult,
) -> List[MethodActivationResult]:
    """Fails & WAKEPY_FAKE_SUCCESS not in use"""
    return method_activation_results3_fail + [mr_wakepy_fake_notinuse]


@pytest.fixture
def method_activation_results4b(
    method_activation_results3_fail: List[MethodActivationResult],
    mr_wakepy_fake_success: MethodActivationResult,
) -> List[MethodActivationResult]:
    """Fails & WAKEPY_FAKE_SUCCESS in use"""
    return method_activation_results3_fail + [mr_wakepy_fake_success]


class TestActivationResult:
    """Tests for ActivationResult"""

    @staticmethod
    @pytest.fixture
    def ar(
        mr_platform_support_fail: MethodActivationResult,
        mr_requirements_fail: MethodActivationResult,
        mr_success_result: MethodActivationResult,
        mr_unused_result: MethodActivationResult,
    ) -> ActivationResult:
        return ActivationResult(
            [
                mr_platform_support_fail,
                mr_requirements_fail,
                mr_success_result,
                mr_unused_result,
            ]
        )

    def test_list_methods_ignore_platform_fails(
        self,
        mr_platform_support_fail: MethodActivationResult,
        mr_requirements_fail: MethodActivationResult,
        mr_success_result: MethodActivationResult,
        mr_unused_result: MethodActivationResult,
        ar: ActivationResult,
    ):
        # By default, the list_methods drops out failures occuring in the
        # platform stage
        assert mr_platform_support_fail not in ar.list_methods()

        # This is what we expect (all but mr_platform_support_fail)
        assert ar.list_methods() == [
            mr_requirements_fail,
            mr_success_result,
            mr_unused_result,
        ]
        # The same as above but with explicit arguments.
        assert ar.list_methods(ignore_platform_fails=True) == [
            mr_requirements_fail,
            mr_success_result,
            mr_unused_result,
        ]
        # Do not ignore platform fails
        assert ar.list_methods(ignore_platform_fails=False) == [
            mr_platform_support_fail,
            mr_requirements_fail,
            mr_success_result,
            mr_unused_result,
        ]

    def test_list_methods_ignore_unused(
        self,
        mr_platform_support_fail: MethodActivationResult,
        mr_requirements_fail: MethodActivationResult,
        mr_success_result: MethodActivationResult,
        mr_unused_result: MethodActivationResult,
        ar: ActivationResult,
    ):
        # Possible to ignore unused methods
        assert mr_unused_result not in ar.list_methods(ignore_unused=True)

        assert ar.list_methods(ignore_platform_fails=False, ignore_unused=True) == [
            mr_platform_support_fail,
            mr_requirements_fail,
            mr_success_result,
        ]

    def test_query_without_args(
        self,
        ar: ActivationResult,
        mr_platform_support_fail: MethodActivationResult,
        mr_requirements_fail: MethodActivationResult,
        mr_success_result: MethodActivationResult,
        mr_unused_result: MethodActivationResult,
    ):

        # When no arguments given, return everything
        assert ar.query() == [
            mr_platform_support_fail,
            mr_requirements_fail,
            mr_success_result,
            mr_unused_result,
        ]

    def test_query_success(
        self,
        ar: ActivationResult,
        mr_platform_support_fail: MethodActivationResult,
        mr_requirements_fail: MethodActivationResult,
    ):
        # Possible to filter with status
        assert ar.query(success=(False,)) == [
            mr_platform_support_fail,
            mr_requirements_fail,
        ]

    def test_query_fail_stages(
        self,
        ar: ActivationResult,
        mr_requirements_fail: MethodActivationResult,
        mr_success_result: MethodActivationResult,
        mr_unused_result: MethodActivationResult,
    ):

        # Possible to filter with fail_stage
        assert ar.query(fail_stages=("REQUIREMENTS",)) == [
            mr_requirements_fail,
            mr_success_result,
            mr_unused_result,
        ]

    def test_query_fail_stages_and_success(
        self,
        ar: ActivationResult,
        mr_requirements_fail: MethodActivationResult,
    ):

        # or with both
        assert ar.query(success=(False,), fail_stages=("REQUIREMENTS",)) == [
            mr_requirements_fail,
        ]

    @pytest.mark.parametrize(
        "method_activation_results, success_expected, real_success_expected",
        [
            ("method_activation_results1", True, True),
            ("method_activation_results2", True, True),
            ("method_activation_results4a", False, False),
            ("method_activation_results4b", True, False),
        ],
    )
    def test_activation_result_success(
        self,
        method_activation_results: List[MethodActivationResult],
        success_expected: bool,
        real_success_expected: bool,
        request,
    ):
        method_activation_results = request.getfixturevalue(method_activation_results)
        with pytest.MonkeyPatch.context():
            ar = ActivationResult(method_activation_results)
            assert ar.success == success_expected
            assert ar.real_success == real_success_expected
            assert ar.failure == (not success_expected)

    def test_get_error_text_success(
        self, method_activation_results1: List[MethodActivationResult]
    ):
        ar = ActivationResult(method_activation_results1)
        # error text is empty string in case of success.
        assert ar.get_error_text() == ""

    def test_get_error_text_failure(
        self,
        mr_platform_support_fail: MethodActivationResult,
        mr_requirements_fail: MethodActivationResult,
    ):
        ar = ActivationResult(
            [mr_platform_support_fail, mr_requirements_fail], modename="SomeMode"
        )
        assert ar.get_error_text() == (
            'Could not activate Mode "SomeMode"!\n\nMethod usage results, in order '
            '(highest priority first):\n[(FAIL @PLATFORM_SUPPORT, fail-platform, "Platform '
            'XYZ not supported!"), (FAIL @REQUIREMENTS, fail-requirements, "Missing '
            'requirement: Some SW v.1.2.3")]'
        )

    def test_active_method(
        self, method_activation_results1: List[MethodActivationResult]
    ):
        ar = ActivationResult(method_activation_results1)
        assert ar.active_method == "a-successful-method"

    def test_active_method_with_fails(
        self,
        mr_platform_support_fail: MethodActivationResult,
        mr_requirements_fail: MethodActivationResult,
    ):
        ar = ActivationResult([mr_platform_support_fail, mr_requirements_fail])
        assert ar.active_method is None

    def test_active_method_with_multiple_success(
        self, method_activation_results2: List[MethodActivationResult]
    ):
        ar = ActivationResult(method_activation_results2)
        with pytest.raises(
            ValueError,
            match=re.escape(
                "The ActivationResult cannot have more than one active methods! Active "
                "methods: ['1st.successful.method', '2nd-successful-method', "
                "'last-successful-method']"
            ),
        ):
            ar.active_method
