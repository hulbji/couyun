def a(len_shi):
    if len_shi % 10 != 0 and len_shi % 14 != 0 or len_shi < 20:
        print(f'aaa{len_shi}')
    else:
        print(f'aaaaaaaaaaa{len_shi}')


if __name__ == '__main__':
    for i in range(100):
        a(i)
