import operator
import sys

from autoscaler.modes.scalemode import AbstractMode
from autoscaler.modes.scalecpu import ScaleByCPU
from autoscaler.modes.scalemem import ScaleByMemory


class ScaleByCPUAndMemory(AbstractMode):

    MODE_NAME = 'and'
    MODE_LIST = ['cpu', 'mem']
    MODES = {
        'cpu': ScaleByCPU,
        'mem': ScaleByMemory
    }

    def __init__(self,  api_client=None, app=None, dimension=None):
        super().__init__(api_client, app)
        self.dimension = dimension

        if len(dimension['min']) < 2 or len(dimension['max']) < 2:
            self.log.error("Scale mode AND requires two comma-delimited "
                           "values for MIN_RANGE and MAX_RANGE.")
            sys.exit(1)

        self.modes = {}
        for idx, mode in enumerate(self.MODE_LIST):
            self.modes[mode] = self.MODES[mode](
                api_client,
                app,
                dimension={
                    'min': dimension['min'][idx],
                    'max': dimension['max'][idx]
                }
            )

    def scale_direction(self):
        results = []
        negative = False

        for mode in self.MODE_LIST:
            d = self.modes[mode].scale_direction()
            if d < 0:
                negative = True
                d = abs(d)
            results.append(d)

        # perform bitwise AND operation on values
        result = operator.and_(results[0], results[1])

        return result if not negative else -result
