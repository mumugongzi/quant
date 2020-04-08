# coding: utf-8
import sys
import time

progress_map = {}


class Progress(object):

    def __init__(self, caller_file_name, caller_file_no, total, step=None, always=True):
        """
        :param caller_file_name: caller文件名
        :param caller_file_no: caller所在文件行号
        :param total: 总共需要调用total次, 进度才完成
        :param step: 每隔step, 打印一次进度, 取值0.01, 每隔1%打印一次进度
        :param always: 每次调用都打印当前进度, step不为None, 该参数才生效
        """
        self.caller_file_name = caller_file_name
        self.caller_file_no = caller_file_no
        self.total = total

        if step is not None:
            self.step = step * 100
            self.next_step = step * 100
        else:
            self.step = None
            self.next_step = None

        self.always = always
        self.progress = 0
        self.start_millis = int(round(time.time() * 1000))

    def get_key(self):
        return self.caller + self.name

    def print(self, **kwargs):

        self.progress = self.progress + 1
        percent = (100 * self.progress) / self.total

        if self.step is not None:
            if percent >= self.next_step:
                print("%s progress: %d%%" % (self.get_msg_prefix(**kwargs), int(percent)))
                while self.next_step <= percent:
                    self.next_step = self.next_step + self.step
        elif self.always:
            print("%s progress: %d/%d" % (self.get_msg_prefix(**kwargs), self.progress, self.total))

    def get_msg_prefix(self, **kwargs):
        cost = int(round(time.time() * 1000)) - self.start_millis

        strs = str(self.caller_file_name).split("/")
        file_name = self.caller_file_name
        if len(strs) > 0:
            file_name = strs[len(strs) - 1]
        res = "File: {} line: {} cost: {}ms ".format(file_name, self.caller_file_no, cost)
        for k, v in kwargs.items():
            res = res + k + "=" + v + " "
        return res

    def is_finish(self):
        return self.progress >= self.total


# 使用方式, 需要在进度循环体时就执行改函数
def print_progress(total, step=None, always=True, **kwargs):
    """
    :param total: 总共需要调用total次, 进度才完成
    :param step: 每隔step, 打印一次进度, 取值0.01, 每隔1%打印一次进度
    :param always: 每次调用都打印当前进度, step不为None, 该参数才生效
    :param kwargs: 需要打印的额外信息
    """
    caller_file_name = sys._getframe(1).f_code.co_filename
    caller_file_no = sys._getframe(1).f_lineno

    key = "{}_{}".format(caller_file_name, caller_file_no)
    if key not in progress_map.keys():
        progress_map[key] = Progress(caller_file_name, caller_file_no, total, step, always)

    progress_obj = progress_map[key]
    progress_obj.print(**kwargs)

    if progress_obj.is_finish():
        del progress_map[key]


if __name__ == "__main__":

    for i in range(100):
        print(100, name="Test1", always=True)

    for i in range(400):
        print(300, step=0.01)
