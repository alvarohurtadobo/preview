import multiprocessing
from playstream import PlayStream

class ParallelPlayStream(multiprocessing.Process,PlayStream):
    def __init__(self):
        super(ParallelCloudSync, self).__init__()