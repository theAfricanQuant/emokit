# -*- encoding: utf-8 -*-

from emokit.tasks import EmotivWriterTask
from emokit.util import values_header, writer_task_to_line

# timestamp + 2 * 14 eeg + 3 gyro = 32
LINE_LENGTH = 32

def _create_EmotivWriterTask():
    item = {"value": 1, "quality": 1}
    header = {head.split(" ")[0] for head in values_header.split(",")}
    data = {head: item for head in header}
    timestamp = "2016-12-20 14:10:49.846000"
    return EmotivWriterTask(data, timestamp=timestamp)

def test_write_task_to_line():
    next_task = _create_EmotivWriterTask()
    line = writer_task_to_line(next_task)
    values = line.split(",")

    assert(len(values) == LINE_LENGTH)

def test_fields():
    header = values_header.split(",")

    assert(len(header) == LINE_LENGTH)
