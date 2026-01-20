"""
判断类
"""
from typing import Union
from decimal import Decimal


class Judgement:
    def __init__(self, expected_values: list, actual_values: list):
        """

        :param expected_values: 期望的值列表
        :param actual_values: 实际值列表
        """
        self.expected_values = expected_values
        self.actual_values = actual_values

    @classmethod
    def judge_single_value(cls, expected_value: Union[int, float], actual_value: Union[int, float]):
        """
        判断单个值
        在这里去掉多余的0
        expected_value --> actual_value

        int --> int
        int --> float 可以接受, float进行取整进行判断
        float -- > int 错误
        float --> float 取两个中最小的小数位数,进行判断

        :param expected_value:
        :param actual_value:
        :return:
        """
        is_pass = False
        expected_value_ = cls._delete_extra_zero(expected_value)
        actual_value_ = cls._delete_extra_zero(actual_value)
        if isinstance(expected_value_, int) and isinstance(actual_value_, int):
            is_pass = True if expected_value_ == actual_value_ else False
        elif isinstance(expected_value_, int) and isinstance(actual_value_, float):
            is_pass = True if expected_value_ == round(actual_value_) else False
        elif isinstance(expected_value_, float) and isinstance(actual_value_, int):
            is_pass = False
        elif isinstance(expected_value_, float) and isinstance(actual_value_, float):
            # 两个都是浮点,按小数位数最小的那个进行判断
            decimal_count = min(cls._count_decimal_places(expected_value_), cls._count_decimal_places(actual_value_))
            # 保留这么多小数位
            expected_value_keep = round(expected_value_, decimal_count)
            actual_value_keep = round(actual_value_, decimal_count)
            # 进行判断
            is_pass = True if expected_value_keep == actual_value_keep else False
        # print(f"期望值:{expected_value} == {actual_value}, --{is_pass}")
        return is_pass

    @classmethod
    def _delete_extra_zero(cls, num: Union[int, float]):
        """
        去掉多余0

        :param num:
        :return:
        """
        num = Decimal(str(num))
        num_ = num.to_integral() if num == num.to_integral() else num.normalize()
        return eval(str(num_))

    @classmethod
    def _count_decimal_places(cls, num):
        """
        计算有几位小数
        :param num:
        :return:
        """
        num_str = str(num)
        # 如果没有小数点，则返回 0
        if '.' not in num_str:
            return 0
        # 使用字符串的 split 方法将字符串分割为整数部分和小数部分
        _, decimal_part = num_str.split('.')
        # 返回小数部分的长度
        return len(decimal_part)

    def judge(self):
        """
        判断
        :return:
        """
        is_pass = True
        if len(self.expected_values) != len(self.actual_values):
            is_pass = False
            return is_pass

        for i, expected_value in enumerate(self.expected_values):
            # 从expected_values中挨个拿出值进行判断
            # 拿出对应的actual_value
            actual_value = self.actual_values[i]
            if not self.judge_single_value(expected_value=expected_value, actual_value=actual_value):
                # 不通过
                is_pass = False
                break
        return is_pass


if __name__ == '__main__':
    except_list = [1, 2, 2.56, 2.37, 2.32]
    actua_list = [1, 2.0000001, 2.555, 2, 2.3199999999]
    x = Judgement(expected_values=except_list, actual_values=actua_list)
    y = x.judge()
    print(f"结果{y}")
