import inspect
from typing import Optional

from buildflow import utils
from buildflow.api import ProcessorAPI, AutoscalingOptions
from buildflow.api.io import SinkType, SourceType
from buildflow.runtime import Runtime
from buildflow.runtime.ray_io import empty_io


class Processor(ProcessorAPI):
    @classmethod
    def sink(self) -> SinkType:
        return empty_io.EmptySink()

    def setup(self):
        pass

    def _process(self, payload):
        return self.process(self.source().preprocess(payload))

    def process(self, payload):
        return payload

    def processor_arg_spec(self):
        return inspect.getfullargspec(self.process)


def processor(
    runtime: Runtime,
    source: SourceType,
    sink: Optional[SinkType] = None,
    num_cpus: float = 0.5,
    autoscaling_options: AutoscalingOptions = AutoscalingOptions(),
):
    if sink is None:
        sink = empty_io.EmptySink()

    def decorator_function(original_function):
        processor_id = original_function.__name__
        # Dynamically define a new class with the same structure as Processor
        class_name = f"AdHocProcessor_{utils.uuid(max_len=8)}"

        def wrapper_function(*args, **kwargs):
            return original_function(*args, **kwargs)

        _AdHocProcessor = type(
            class_name,
            (object,),
            {
                "source": lambda self: source,
                "sink": lambda self: sink,
                "sinks": lambda self: [],
                "setup": lambda self: None,
                "process": lambda self, payload: original_function(payload),
                "processor_arg_spec": lambda self: inspect.getfullargspec(
                    original_function
                ),
                "_process": lambda self, payload: original_function(
                    self.source().preprocess(payload)
                ),
                "num_cpus": lambda self: num_cpus,
                "__call__": wrapper_function,
                "autoscaling_options": lambda self: autoscaling_options,
            },
        )
        processor_instance = _AdHocProcessor()
        runtime.register_processor(processor_instance, processor_id=processor_id)

        return processor_instance

    return decorator_function
