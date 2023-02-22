"""Sample usage of buildflow.

steps to run:
    1. pip install .
    2. gcloud auth application-default login
    3. python sample.py
"""

import buildflow as flow

# TODO(developer): Fill in with a pub/sub subscription.
_SUBSCRIPTION = 'TODO'


class MyProcessor(flow.Processor):

    @staticmethod
    def _input():
        return flow.PubSub(subscription=_SUBSCRIPTION)

    def _setup(self):
        # this is where you would initialize any clients / shared state
        self.client = ...

    def process(self, taxi_info):
        print(taxi_info)
        return taxi_info


flow.run(MyProcessor)
