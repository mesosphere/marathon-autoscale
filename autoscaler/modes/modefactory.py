import sys

from autoscaler.modes.scalecpu import ScaleByCPU
from autoscaler.modes.scalesqs import ScaleBySQS
from autoscaler.modes.scalemem import ScaleByMemory
from autoscaler.modes.scalecpuandmem import ScaleByCPUAndMemory


class ModeFactory:

    # Dictionary defines the different scaling modes available to autoscaler
    MODES = {
        'sqs': ScaleBySQS,
        'cpu': ScaleByCPU,
        'mem': ScaleByMemory,
        'and': ScaleByCPUAndMemory
    }

    @staticmethod
    def create_mode(self, mode_name, api_client, app, dimension):

        if self.MODES.get(mode_name, None) is None:
            self.log.error("Scale mode is not found.")
            sys.exit(1)

        mode = self.MODES[mode_name](api_client, app, dimension)

        return mode
