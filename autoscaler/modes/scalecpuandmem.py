import operator

from autoscaler.modes.scalemode import AbstractMode
from autoscaler.modes.modefactory import ModeFactory


class ScaleByCPUAndMemory(AbstractMode):

    MODE_NAME = 'and'
    MODE_LIST = ['cpu', 'mem']

    def __init__(self,  api_client=None, app=None, dimension=None):
        super().__init__(api_client, app)
        self.dimension = dimension

        modes = {}
        for idx, mode in enumerate(self.MODE_LIST):
            modes[mode] = ModeFactory.MODES[mode](
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
            inst = self.modes[mode]
            dir = inst.scale_direction()
            if dir < 0:
                negative = True
                dir = abs(dir)
            results.append(dir)

        # perform bitwise operation on values
        result = operator.and_(results)
        r = result if not negative else -result

        return r
