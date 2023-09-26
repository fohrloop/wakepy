from queue import Queue
from wakepy.core import ActivationResult, Method, StageName
from wakepy.core.activationresult import WorkerThreadMsgType


class MethodA(Method):
    ...


def mock_check_platform_support(method: Method):
    return isinstance(method, MethodA)


def mock_check_requirements_support(method: Method):
    return isinstance(method, MethodA)


def mock_activate_mode(method: Method):
    return isinstance(method, MethodA)


def test_activation_result_with_one_method():
    method_a = MethodA()
    q = Queue()

    methods = [method_a]

    ar = ActivationResult(candidate_methods=methods, queue_thread=q)

    def put_to_queue(data):
        q.put((WorkerThreadMsgType.OK, data))

    # Mock the ModeWorkerThread
    for method in methods:
        put_to_queue(
            (
                StageName.PLATFORM_SUPPORT,
                id(method),
                mock_check_platform_support(method),
            )
        )
        put_to_queue(
            (
                StageName.REQUIREMENTS,
                id(method),
                mock_check_requirements_support(method),
            )
        )
        put_to_queue(
            (
                StageName.ACTIVATION,
                id(method),
                mock_check_requirements_support(method),
            )
        )
        put_to_queue((StageName.WAITING_EXIT,))

    assert ar.success
