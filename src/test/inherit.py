# coding: utf-8
from abc import abstractmethod


# print(True & 0)

a = 'a'
print(a != 'a')


class Parent(object):

    def __init__(self):
        pass

    def run(self):
        self.imp()

    def imp(self):
        print("I'm parent")


class Child(Parent):

    def __init__(self):
        pass

    def imp(self):
        super().imp()
        print("I'm child")


if __name__ == '__main__':
    a = Child()
    a.run()
