import sys
import operator


from autoscaler.modes.abstractmode import AbstractMode
from autoscaler.modes.scalecpu import ScaleByCPU
from autoscaler.modes.scalemem import ScaleByMemory


class ScaleByCPUOrMemory(AbstractMode):

    def __init__(self,  api_client=None, agent_stats=None, app=None,
                 dimension=None):
        super().__init__(api_client, agent_stats, app)
        self.mode_map = {'cpu': ScaleByCPU, 'mem': ScaleByMemory}

        if len(dimension['min']) < 2 or len(dimension['max']) < 2:
            self.log.error("Scale mode OR requires two comma-delimited "
                           "values for MIN_RANGE and MAX_RANGE.")
            sys.exit(1)

        # Instantiate the CPU/Memory mode classes
        for idx, mode in enumerate(list(self.mode_map.keys())):
            self.mode_map[mode] = self.mode_map[mode](
                api_client,
                app,
                dimension={
                    'min': dimension['min'][idx],
                    'max': dimension['max'][idx]
                }
            )

    def scale_direction(self):
        """
        Performs a bitwise OR on the returned direction from CPU (x)
        and Memory (y). If x = -1 and y = 1, returned direction will be -1.
        """
        results = []

        try:
            for mode in list(self.mode_map.keys()):
                results.append(self.mode_map[mode].scale_direction())
        except ValueError:
            raise

        self.log.info("CPU direction = %s, Memory direction = %s",
                      results[0], results[1])

        # perform bitwise OR operation on CPU and Memory direction
        return operator.or_(results[0], results[1])
