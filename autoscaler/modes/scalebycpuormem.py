import sys
import operator


from autoscaler.modes.abstractmode import AbstractMode
from autoscaler.modes.scalecpu import ScaleByCPU
from autoscaler.modes.scalemem import ScaleByMemory


class ScaleByCPUOrMemory(AbstractMode):

    def __init__(self,  api_client=None, app=None, dimension=None):
        super().__init__(api_client, app)
        self.dimension = dimension
        self.mode_map = {'cpu': ScaleByCPU, 'mem': ScaleByMemory}

        if len(dimension['min']) < 2 or len(dimension['max']) < 2:
            self.log.error("Scale mode AND requires two comma-delimited "
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
        and Memory (y). If (x = y = 0), return 0, otherwise
        return -1 or 1. If (x = -1, y = 1), return -1.
        """
        results = []

        for mode in list(self.mode_map.keys()):
            results.append(self.mode_map[mode].scale_direction())

        # perform bitwise OR operation on CPU and Memory direction
        return operator.or_(results[0], results[1])
