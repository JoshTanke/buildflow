import unittest
from unittest import mock

from buildflow.api import options
from buildflow.runtime.managers import auto_scaler


@mock.patch('ray.cluster_resources', return_value={'CPU': 32})
class AutoScalerTest(unittest.TestCase):

    def test_scale_up_to_estimated_replicas(self, resources_mock):
        current_num_replicas = 3
        backlog = 100_000
        # 12_000 events per minute means we can burn down a backlog 12_000
        # in one minute so our estimated number of replicas would be 16
        # (100_000 / 12_00).
        events_processed_per_replica = [12_000] * 3
        non_empty_ratio_per_replica = [1] * 3

        rec_replicas = auto_scaler.get_recommended_num_replicas(
            current_num_replicas=current_num_replicas,
            backlog=backlog,
            events_processed_per_replica=events_processed_per_replica,
            non_empty_ratio_per_replica=non_empty_ratio_per_replica,
            time_since_last_check=60,
            source_cpus=.25,
            autoscaling_options=options.StreamingOptions(),
        )

        self.assertEqual(8, rec_replicas)

    def test_scale_down_to_estimated_replicas(self, resources_mock):
        current_num_replicas = 24
        backlog = 100_000
        # 15_000 events per minute means we can burn down a backlog 15_000
        # in minute so our estimated number of replicas would be 6
        # (100_000 / 15_000).
        events_processed_per_replica = [15_000] * 24
        # Our non empty ratio is low meaning we have low utilization so we will
        # attempt to scale down. With this ratio we would scale down to 2
        # replica, but based on the backlog we will keep 8 replicas to ensure
        # the backlog can be burned down.
        non_empty_ratio_per_replica = [.1] * 24

        rec_replicas = auto_scaler.get_recommended_num_replicas(
            current_num_replicas=current_num_replicas,
            backlog=backlog,
            events_processed_per_replica=events_processed_per_replica,
            non_empty_ratio_per_replica=non_empty_ratio_per_replica,
            time_since_last_check=60,
            source_cpus=.25,
            autoscaling_options=options.StreamingOptions(),
        )

        self.assertEqual(6, rec_replicas)

    def test_scale_up_to_max_options_replicas(self, resources_mock):
        current_num_replicas = 3
        backlog = 100_000
        # 12_000 events per minute means we can burn down a backlog 12_000
        # in minute so our estimated number of replicas would be 8
        # (100_000 / 12_00).
        events_processed_per_replica = [12_000] * 3
        non_empty_ratio_per_replica = [1] * 3

        rec_replicas = auto_scaler.get_recommended_num_replicas(
            current_num_replicas=current_num_replicas,
            backlog=backlog,
            events_processed_per_replica=events_processed_per_replica,
            non_empty_ratio_per_replica=non_empty_ratio_per_replica,
            time_since_last_check=60,
            source_cpus=.25,
            # Max replicas will cap recommendation. Even though we need 8 to
            # burn down the backlog we won't scale beyond max_replicas.
            autoscaling_options=options.StreamingOptions(max_replicas=5),
        )

        self.assertEqual(5, rec_replicas)

    def test_scale_up_to_max_cpu_replicas(self, resources_mock):
        current_num_replicas = 3
        backlog = 100_000
        # 100 events per minute means we can burn down a backlog 100
        # in minute so our estimated number of replicas would be 1000
        # (100_000 / 100).
        # However this will be limited by the number of CPUs on our cluster.
        # We have 32 CPUs in our mock cluster, so we will only scale to:
        #   32 / .25 * .66 = 84
        #   num_cpus / source_cpus / REPLICA_CPU_RATION
        events_processed_per_replica = [100] * 3
        non_empty_ratio_per_replica = [1] * 3

        rec_replicas = auto_scaler.get_recommended_num_replicas(
            current_num_replicas=current_num_replicas,
            backlog=backlog,
            events_processed_per_replica=events_processed_per_replica,
            non_empty_ratio_per_replica=non_empty_ratio_per_replica,
            time_since_last_check=60,
            source_cpus=.25,
            autoscaling_options=options.StreamingOptions(),
        )

        self.assertEqual(84, rec_replicas)

    def test_scale_down_to_target_utilization(self, resources_mock):
        current_num_replicas = 24
        backlog = 10
        # 15_000 events per minute means we can burn down a backlog 15_000
        # in minute so our estimated number of replicas would be 6
        # (10 / 15_000).
        events_processed_per_replica = [15_000] * 24
        # Our non empty ratio is low meaning we have low utilization so we will
        # attempt to scale down. With this ratio we would scale down to 15
        # replicas to achieve a utilization of .5
        non_empty_ratio_per_replica = [.3] * 24

        rec_replicas = auto_scaler.get_recommended_num_replicas(
            current_num_replicas=current_num_replicas,
            backlog=backlog,
            events_processed_per_replica=events_processed_per_replica,
            non_empty_ratio_per_replica=non_empty_ratio_per_replica,
            time_since_last_check=60,
            source_cpus=.25,
            autoscaling_options=options.StreamingOptions(),
        )

        self.assertEqual(15, rec_replicas)

    def test_scale_down_to_min_options_replicas(self, resources_mock):
        current_num_replicas = 24
        backlog = 10
        # 15_000 events per minute means we can burn down a backlog 15_000
        # in minute so our estimated number of replicas would be 6
        # (10 / 15_000).
        events_processed_per_replica = [15_000] * 24
        # Our non empty ratio is low meaning we have low utilization so we will
        # attempt to scale down. With this ratio we would scale down to 6
        # replicas to achieve a utilization of .75
        non_empty_ratio_per_replica = [.3] * 24

        rec_replicas = auto_scaler.get_recommended_num_replicas(
            current_num_replicas=current_num_replicas,
            backlog=backlog,
            events_processed_per_replica=events_processed_per_replica,
            non_empty_ratio_per_replica=non_empty_ratio_per_replica,
            time_since_last_check=120,
            source_cpus=.25,
            # Don't scale below 18 replicas.
            autoscaling_options=options.StreamingOptions(min_replicas=18),
        )

        self.assertEqual(18, rec_replicas)


if __name__ == '__name__':
    unittest.main()
