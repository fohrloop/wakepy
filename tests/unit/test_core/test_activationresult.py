from __future__ import annotations

import re
import typing

import pytest

from wakepy.core import ActivationResult, MethodActivationResult
from wakepy.core.constants import StageName
from wakepy.core.registry import get_method

if typing.TYPE_CHECKING:
    from typing import List

fake_success_cls = get_method("WAKEPY_FAKE_SUCCESS")

TEST_MODE = "test-mode"


@pytest.fixture
def mr_platform_support_fail() -> MethodActivationResult:
    return MethodActivationResult(
        success=False,
        failure_stage=StageName.PLATFORM_SUPPORT,
        method_name="fail-platform",
        mode_name=TEST_MODE,
        failure_reason="Platform XYZ not supported!",
    )


@pytest.fixture
def mr_requirements_fail() -> MethodActivationResult:
    return MethodActivationResult(
        success=False,
        failure_stage=StageName.REQUIREMENTS,
        method_name="fail-requirements",
        mode_name=TEST_MODE,
        failure_reason="Missing requirement: Some SW v.1.2.3",
    )


@pytest.fixture
def mr_success_result() -> MethodActivationResult:
    return MethodActivationResult(
        success=True,
        method_name="a-successful-method",
        mode_name=TEST_MODE,
    )


@pytest.fixture
def mr_unused_result() -> MethodActivationResult:
    return MethodActivationResult(
        success=None,
        method_name="some-unused-method",
        mode_name=TEST_MODE,
    )


@pytest.fixture
def mr_wakepy_fake_notinuse() -> MethodActivationResult:
    return MethodActivationResult(
        success=False,
        failure_stage=StageName.ACTIVATION,
        method_name=fake_success_cls.name,
        mode_name=TEST_MODE,
    )


@pytest.fixture
def mr_wakepy_fake_success() -> MethodActivationResult:
    return MethodActivationResult(
        success=True,
        failure_stage=StageName.ACTIVATION,
        method_name=fake_success_cls.name,
        mode_name=TEST_MODE,
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
def method_activation_results2_manysuccess(
    mr_requirements_fail: MethodActivationResult,
) -> List[MethodActivationResult]:
    return [
        MethodActivationResult(
            success=True,
            method_name="1st.successful.method",
            mode_name=TEST_MODE,
        ),
        # Fails in Requirement stage
        mr_requirements_fail,
        MethodActivationResult(
            success=True,
            method_name="2nd-successful-method",
            mode_name=TEST_MODE,
        ),
        MethodActivationResult(
            success=True,
            method_name="last-successful-method",
            mode_name=TEST_MODE,
        ),
    ]


@pytest.fixture
def method_activation_results3_fail() -> List[MethodActivationResult]:
    return [
        MethodActivationResult(
            success=False,
            failure_stage=StageName.PLATFORM_SUPPORT,
            method_name="fail-platform",
            mode_name=TEST_MODE,
            failure_reason="Platform XYZ not supported!",
        ),
        MethodActivationResult(
            success=False,
            failure_stage=StageName.REQUIREMENTS,
            method_name="fail-requirements",
            mode_name=TEST_MODE,
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

    def test_get_failure_text_success(
        self, method_activation_results1: List[MethodActivationResult]
    ):
        ar = ActivationResult(method_activation_results1)
        # error text is empty string in case of success.
        assert ar.get_failure_text() == ""

    def test_get_failure_text_failure(
        self,
        mr_platform_support_fail: MethodActivationResult,
        mr_requirements_fail: MethodActivationResult,
    ):
        ar = ActivationResult(
            [mr_platform_support_fail, mr_requirements_fail], mode_name="SomeMode"
        )
        assert ar.get_failure_text() == (
            'Could not activate Mode "SomeMode"!\n\nMethod usage results, in order '
            "(highest priority first):\n[(FAIL @PLATFORM_SUPPORT, fail-platform, "
            '"Platform XYZ not supported!"), (FAIL @REQUIREMENTS, fail-requirements, '
            '"Missing requirement: Some SW v.1.2.3")]'
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
        self, method_activation_results2_manysuccess: List[MethodActivationResult]
    ):
        with pytest.raises(
            ValueError,
            match=re.escape(
                "The ActivationResult cannot have more than one active methods! Active "
                "methods: ['1st.successful.method', '2nd-successful-method', "
                "'last-successful-method']"
            ),
        ):
            ActivationResult(method_activation_results2_manysuccess)

    @pytest.mark.parametrize(
        "method_activation_results",
        [
            ("method_activation_results1"),
            ("method_activation_results3_fail"),
            ("method_activation_results4a"),
            ("method_activation_results4b"),
        ],
    )
    def test__eq__(
        self, method_activation_results: List[MethodActivationResult], request
    ):
        method_activation_results = request.getfixturevalue(method_activation_results)
        ar1 = ActivationResult(method_activation_results, mode_name="foo")
        ar2 = ActivationResult(method_activation_results, mode_name="foo")

        assert ar1 is not ar2
        assert ar1 == ar2

    def test__repr__(self, method_activation_results1: List[MethodActivationResult]):
        ar1 = ActivationResult(method_activation_results1, mode_name="foo")
        assert (
            ar1.__repr__()
            == """ActivationResult(mode_name='foo', active_method='a-successful-method', success=True, real_success=True, failure=False, _method_results=[(FAIL @PLATFORM_SUPPORT, fail-platform, "Platform XYZ not supported!"), (FAIL @REQUIREMENTS, fail-requirements, "Missing requirement: Some SW v.1.2.3"), (SUCCESS, a-successful-method), (UNUSED, some-unused-method)])"""  # noqa: E501
        )


class TestMethodActivationResult:
    """Tests for MethodActivationResult"""

    @pytest.fixture
    def a(self) -> MethodActivationResult:
        return MethodActivationResult(
            method_name="foo",
            mode_name=TEST_MODE,
            success=False,
            failure_stage=StageName.REQUIREMENTS,
            failure_reason="some-text",
        )

    @pytest.fixture
    def b(self) -> MethodActivationResult:
        return MethodActivationResult(
            method_name="foo",
            mode_name=TEST_MODE,
            success=False,
            failure_stage=StageName.REQUIREMENTS,
            failure_reason="some-text",
        )

    def test_equality_check_similar(
        self, a: MethodActivationResult, b: MethodActivationResult
    ):
        # MethodActivationResult implements __eq__
        assert a is not b
        assert a == b

    @pytest.fixture
    def c_different_method_name(self) -> MethodActivationResult:
        return MethodActivationResult(
            method_name="bar",
            mode_name=TEST_MODE,
            success=False,
            failure_stage=StageName.REQUIREMENTS,
            failure_reason="some-text",
        )

    @pytest.fixture
    def c_different_success(self) -> MethodActivationResult:
        return MethodActivationResult(
            method_name="foo",
            mode_name=TEST_MODE,
            success=True,
            failure_stage=StageName.REQUIREMENTS,
            failure_reason="some-text",
        )

    @pytest.fixture
    def c_different_failure_stage(self) -> MethodActivationResult:
        return MethodActivationResult(
            method_name="foo",
            mode_name=TEST_MODE,
            success=False,
            failure_stage=StageName.PLATFORM_SUPPORT,
            failure_reason="some-text",
        )

    @pytest.fixture
    def c_different_failure_reason(self) -> MethodActivationResult:
        return MethodActivationResult(
            method_name="foo",
            mode_name=TEST_MODE,
            success=False,
            failure_stage=StageName.REQUIREMENTS,
            failure_reason="some-other-text",
        )

    def test_equality_check_different(
        self,
        a: MethodActivationResult,
        c_different_method_name: MethodActivationResult,
        c_different_success: MethodActivationResult,
        c_different_failure_stage: MethodActivationResult,
        c_different_failure_reason: MethodActivationResult,
    ):

        c_list = [
            c_different_method_name,
            c_different_success,
            c_different_failure_stage,
            c_different_failure_reason,
        ]
        # MethodActivationResult implements __eq__
        assert all(isinstance(x, MethodActivationResult) for x in [a] + c_list)
        for c in c_list:
            assert a != c

    def test_repr(self, a: MethodActivationResult):
        assert a.__repr__() == '(FAIL @REQUIREMENTS, foo, "some-text")'
