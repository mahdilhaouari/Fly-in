# a test that show that when we not initialise the objects created 
# from the same class the store the data in the same object
class test:
    def __init__(self, list: list = []) -> None:
        self.list = list


test1 = test()
test2 = test()

print(f"{test1.list} AND {test2.list}")

print(test1.list is test2.list)
test1.list.append(3)

print(f"{test1.list} AND {test2.list}")
