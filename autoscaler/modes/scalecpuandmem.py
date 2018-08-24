import operator

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

        modes = {}
        for idx, mode in enumerate(self.MODE_LIST):
            modes[mode] = self.MODES[mode](
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
        result = operator.and_(results)

        return result if not negative else -result
