import logging


class AgentStats:
    def __init__(self, api_client):
        self.api_client = api_client
        self.stats = {}
        self.log = logging.getLogger("autoscale")

    def reset(self):
        """ Drop all cached statistics.
        """
        self.stats = {}

    def get_task_stats(self, agent, task, n=0):
        """ Get the performance metrics of the given task running on
        the specified agent. If the n'th snapshot is cached, it is
        returned, otherwise a request to the agent is made.
        Args:
            task: marathon app task
            agent: agent on which the task is run
            n: statistics snapshot index
        Returns:
            statistics snapshot for the specific task running on the agent
        """

        agent_stats = self.stats.get(agent, [])
        assert len(agent_stats) >= n, \
            'n must be one of indexes of snapshots fetched previosly or be ' + \
            'greater by one to fetch a new snapshot'

        if len(agent_stats) > n:
            snapshot = agent_stats[n]
        else:
            snapshot = self.api_client.dcos_rest(
                "get",
                '/slave/' + agent + '/monitor/statistics'
            )
            agent_stats.append(snapshot)
            self.stats[agent] = agent_stats

        for i in snapshot:
            executor_id = i['executor_id']
            if executor_id == task:
                task_stats = i['statistics']
                self.log.debug("stats for task %s agent %s: %s",
                               executor_id, agent, task_stats)
                return task_stats
