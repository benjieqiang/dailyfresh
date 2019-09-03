from django.test import TestCase

# Create your tests here.

#类中添加对象属性
class Test():
    def __init__(self):
        self.name = 'alex'
t = Test()
print(t.name)
t.age = '121'
print(t.age)