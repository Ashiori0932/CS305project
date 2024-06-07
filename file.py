import random

def generate_random_numbers(file_name, count):
    with open(file_name, 'w') as file:
        for _ in range(count):
            number = random.randint(0, 9)
            file.write(f"{number}")

# 调用函数生成文件
generate_random_numbers('original.txt', 100000)
