#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import argparse
import csv
import inspect
import os
import re
import signal
from enum import Enum

from happy_python import HappyLog
from happy_python import HappyPyException
from happy_python import dict_to_pretty_json
from happy_python import execute_cmd
from happy_python.happy_log import HappyLogLevel

log = HappyLog.get_instance()
__version__ = '1.0.3'
NULL_VALUE = 'NULL'
line_number = 0

# 变量暂存区
_var_tmp_storage_area = dict()


def _output_message_builder(row_id: str, message: str, status: bool):
    return '编号：%s -> %s...[ %s ]' % (row_id, message, ('OK' if status else 'FAILED'))


def _is_alpha_num_underline_str(value: str):
    return bool(re.match(r'^\w+$', value))


def _make_error_message(row_desc: str, col_name: str, value_desc: str):
    msg = '第%d行->%s模式的行，"%s"列应为"%s"' % (line_number, row_desc, col_name, value_desc)
    raise HappyPyException(msg)


def _make_error_message_required(row_desc: str, col_name: str):
    msg = '第%d行->%s模式的行，"%s"列需要指定值' % (line_number, row_desc, col_name)
    raise HappyPyException(msg)


def _replace_var(row_id: str, s: str) -> (bool, str):
    tmp = s
    var_dict = {**_var_tmp_storage_area, **os.environ}

    # 从暂存区读取变量值 & 从环境变量中读取变量值
    for var_name, var_value in var_dict.items():
        var_expr = '${%s}' % var_name
        index = tmp.find(var_expr)

        if index != -1:
            if var_value == '' or var_value is None:
                log.error('替换变量时出现空值：%s -> %s，type=%s' % (var_name, var_value, type(var_value)))
                raise HappyPyException(_output_message_builder(row_id, tmp, False))

            tmp = tmp.replace(var_expr, var_value)

    m = re.match(r'.*(\${[a-zA-Z\d_]+}).*', tmp)

    if m:
        log.error('存在未替换的变量：%s' % m.group(1))
        raise HappyPyException(_output_message_builder(row_id, tmp, False))

    return tmp


class ColInfo(Enum):
    RowID = '编号'
    ModeType = '模式'
    CmdLine = '命令'
    ReturnCode = '返回代码'
    ReturnType = '返回类型'
    DefaultValue = '默认值'
    ReturnFilter = '过滤器'
    VarName = '变量名'
    Message = '提示消息'
    __order__ = 'RowID ModeType CmdLine ReturnCode ReturnType DefaultValue ReturnFilter VarName Message'


class ModeType(Enum):
    CONST = 0
    VAR = 1
    ENV = 2
    CMD = 3
    MESSAGE = 4
    STATEMENT = 5


class ReturnType(Enum):
    NULL = 0
    INT = 1
    STR = 2


class CsvRow:
    def __init__(self,
                 row_id: str,
                 mode_type: ModeType,
                 cmd_line: str,
                 return_code: int,
                 return_type: ReturnType,
                 default_value: str,
                 return_filter: str,
                 var_name: str,
                 message: str):
        self.row_id = row_id
        self.mode_type: ModeType = mode_type
        self.cmd_line = cmd_line
        self.return_code = return_code
        self.return_type = return_type
        self.default_value = default_value
        # 使用正则表达式从命令执行中过滤出需要的部分
        self.return_filter = return_filter
        self.var_name = var_name
        self.message = message


class ColValidator:
    @staticmethod
    def validate_row_id(value: str):
        if not (value and (value == NULL_VALUE or _is_alpha_num_underline_str(value))):
            msg = '第%d行->%s：无效值"%s"，只能由数字、字母和下划线组成' % (line_number, ColInfo.RowID.value, value)
            raise HappyPyException(msg)

    @staticmethod
    def validate_mode_type(value: str):
        try:
            # noinspection PyUnusedLocal
            tmp = ModeType[value]
        except KeyError:
            msg = '第%d行->%s：无效值"%s"，可选值为CONST_VAR、VAR、ENV和CMD' % (line_number, ColInfo.ModeType.value, value)
            raise HappyPyException(msg)

    @staticmethod
    def validate_cmd_line(value: str):
        if not (value or value == NULL_VALUE):
            msg = '第%d行->%s：无效值"%s"，可以为NULL或非字符串' % (line_number, ColInfo.CmdLine.value, value)
            raise HappyPyException(msg)

    @staticmethod
    def validate_return_code(value: str):
        if not (value and (value == NULL_VALUE or value.isdigit())):
            msg = '第%d行->%s：无效值"%s"，只能是数字' % (line_number, ColInfo.ReturnCode.value, value)
            raise HappyPyException(msg)

    @staticmethod
    def validate_return_type(value: str):
        try:
            # noinspection PyUnusedLocal
            tmp = ReturnType[value]
        except KeyError:
            msg = '第%d行->%s：无效值"%s"，可选值为NULL、INT、STR' % (line_number, ColInfo.ReturnType.value, value)
            raise HappyPyException(msg)

    @staticmethod
    def validate_default_value(value: str):
        if not (value or value == NULL_VALUE):
            msg = '第%d行->%s：无效值"%s"，可以为NULL或非空字符串' % (line_number, ColInfo.DefaultValue.value, value)
            raise HappyPyException(msg)

    @staticmethod
    def validate_return_filter(value: str):
        if not (value or value == NULL_VALUE):
            msg = '第%d行->%s：无效值"%s"，可以为NULL或不为空的字符串' % (line_number, ColInfo.ReturnFilter.value, value)
            raise HappyPyException(msg)

    @staticmethod
    def validate_var_name(value: str):
        if not (value and (value == NULL_VALUE or _is_alpha_num_underline_str(value))):
            msg = '第%d行->%s：无效值"%s"，只能由数字、字母和下划线组成' % (line_number, ColInfo.VarName.value, value)
            raise HappyPyException(msg)

    @staticmethod
    def validate_message(value: str):
        if not value:
            msg = '第%d行->%s：无效值"%s"，只能是非空字符串' % (line_number, ColInfo.Message.value, value)
            raise HappyPyException(msg)


class RowValidator:
    @staticmethod
    def validate_const_row(row: CsvRow):
        assert row.mode_type == ModeType.CONST
        row_desc = '常量'

        if row.cmd_line != NULL_VALUE:
            _make_error_message(row_desc, ColInfo.CmdLine.value, NULL_VALUE)

        if row.return_code != NULL_VALUE:
            _make_error_message(row_desc, ColInfo.ReturnCode.value, NULL_VALUE)

        if row.return_type == ReturnType.NULL:
            _make_error_message_required(row_desc, ColInfo.ReturnType.value)

        if not row.default_value or row.default_value == NULL_VALUE:
            _make_error_message_required(row_desc, ColInfo.DefaultValue.value)

        if row.return_filter != NULL_VALUE:
            _make_error_message(row_desc, ColInfo.ReturnFilter.value, NULL_VALUE)

        if row.var_name == NULL_VALUE:
            _make_error_message_required(row_desc, ColInfo.VarName.value)

        if row.message == NULL_VALUE:
            _make_error_message_required(row_desc, ColInfo.Message.value)

    @staticmethod
    def validate_message_row(row: CsvRow):
        assert row.mode_type == ModeType.MESSAGE
        row_desc = '消息'

        if row.cmd_line != NULL_VALUE:
            _make_error_message(row_desc, ColInfo.CmdLine.value, NULL_VALUE)

        if row.return_code != NULL_VALUE:
            _make_error_message(row_desc, ColInfo.ReturnCode.value, NULL_VALUE)

        if row.return_type != ReturnType.NULL:
            _make_error_message(row_desc, ColInfo.ReturnType.value, NULL_VALUE)

        if row.default_value != NULL_VALUE:
            _make_error_message(row_desc, ColInfo.DefaultValue.value, NULL_VALUE)

        if row.return_filter != NULL_VALUE:
            _make_error_message(row_desc, ColInfo.ReturnFilter.value, NULL_VALUE)

        if row.var_name != NULL_VALUE:
            _make_error_message(row_desc, ColInfo.VarName.value, NULL_VALUE)

        if row.message == NULL_VALUE:
            _make_error_message_required(row_desc, ColInfo.Message.value)

    @staticmethod
    def validate_env_row(row: CsvRow):
        assert row.mode_type == ModeType.ENV
        row_desc = '环境变量'

        if row.cmd_line != NULL_VALUE:
            _make_error_message(row_desc, ColInfo.CmdLine.value, NULL_VALUE)

        if row.return_code != NULL_VALUE:
            _make_error_message(row_desc, ColInfo.ReturnCode.value, NULL_VALUE)

        if row.return_type != ReturnType.NULL:
            _make_error_message(row_desc, ColInfo.ReturnType.value, NULL_VALUE)

        if row.default_value == NULL_VALUE:
            _make_error_message_required(row_desc, ColInfo.DefaultValue.value)

        if row.return_filter != NULL_VALUE:
            _make_error_message(row_desc, ColInfo.ReturnFilter.value, NULL_VALUE)

        if row.var_name == NULL_VALUE:
            _make_error_message_required(row_desc, ColInfo.VarName.value)

        if row.message == NULL_VALUE:
            _make_error_message_required(row_desc, ColInfo.Message.value)

    @staticmethod
    def validate_cmd_row(row: CsvRow):
        assert row.mode_type == ModeType.CMD
        row_desc = '命令'

        if row.cmd_line == NULL_VALUE:
            _make_error_message_required(row_desc, ColInfo.CmdLine.value)

        if row.return_code == NULL_VALUE:
            _make_error_message_required(row_desc, ColInfo.ReturnCode.value)

        # 忽略 row.return_type

        if row.default_value != NULL_VALUE:
            _make_error_message(row_desc, ColInfo.DefaultValue.value, NULL_VALUE)

        if row.return_filter != NULL_VALUE:
            # 设置了过滤器时，必须指定变量名和返回类型
            if row.var_name == NULL_VALUE:
                _make_error_message_required(row_desc, ColInfo.VarName.value)

            if row.return_type == NULL_VALUE:
                _make_error_message_required(row_desc, ColInfo.ReturnType.value)
        else:
            # 其它情况忽略 row.var_name
            pass

        # 设置了变量名时，必须设置返回类型
        if row.var_name != NULL_VALUE:
            if row.return_type == NULL_VALUE:
                _make_error_message_required(row_desc, ColInfo.ReturnType.value)

        if row.message == NULL_VALUE:
            _make_error_message_required(row_desc, ColInfo.Message.value)

    @staticmethod
    def validate_statement_row(row: CsvRow):
        assert row.mode_type == ModeType.STATEMENT
        row_desc = '语句'

        if row.cmd_line == NULL_VALUE:
            _make_error_message_required(row_desc, ColInfo.CmdLine.value)

        if row.return_code != NULL_VALUE:
            _make_error_message(row_desc, ColInfo.ReturnCode.value, NULL_VALUE)

        # 忽略 row.default_value
        # 忽略 row.return_filter

        if row.var_name != NULL_VALUE:
            if row.return_type == NULL_VALUE:
                _make_error_message_required(row_desc, ColInfo.ReturnType.value)

        if row.message == NULL_VALUE:
            _make_error_message_required(row_desc, ColInfo.Message.value)


class RowHandler:
    @staticmethod
    def const_handler(row: CsvRow):
        global _var_tmp_storage_area

        fn_name = inspect.stack()[0][3]
        log.enter_func(fn_name)

        log.var('row', row)

        row_id = row.row_id
        message = _replace_var(row_id, row.message)
        log.var('row_id', row_id)
        log.var('message', message)

        var_name = row.var_name
        var_value = _replace_var(row_id, row.default_value)
        log.var('var_name', var_name)
        log.var('var_value', var_value)

        if row.return_type == ReturnType.INT:
            _var_tmp_storage_area[var_name] = int(var_value)
        elif row.return_type == ReturnType.STR:
            _var_tmp_storage_area[var_name] = var_value
        else:
            _var_tmp_storage_area[var_name] = var_value

        log.info(_output_message_builder(row_id, message, True))

        log.exit_func(fn_name)

    @staticmethod
    def message_handler(row: CsvRow):
        fn_name = inspect.stack()[0][3]
        log.enter_func(fn_name)

        log.var('row', row)

        row_id = row.row_id
        message = _replace_var(row_id, row.message)
        log.var('row_id', row_id)
        log.var('message', message)

        log.info(_output_message_builder(row_id, message, True))

        log.exit_func(fn_name)

    @staticmethod
    def env_handler(row: CsvRow):
        import os
        fn_name = inspect.stack()[0][3]
        log.enter_func(fn_name)

        log.var('row', row)

        row_id = row.row_id
        message = _replace_var(row_id, row.message)
        log.var('row_id', row_id)
        log.var('message', message)

        env_name = row.var_name
        env_value = _replace_var(row_id, row.default_value)
        log.var('env_name', env_name)
        log.var('env_value', env_value)

        try:
            os.environ[env_name] = env_value
            log.info(_output_message_builder(row_id, message, True))
        except Exception as e:
            log.critical(e)
            raise HappyPyException(_output_message_builder(row_id, message, False))

        log.exit_func(fn_name)

    @staticmethod
    def cmd_handler(row: CsvRow):
        fn_name = inspect.stack()[0][3]
        log.enter_func(fn_name)

        log.var('row', row)

        row_id = row.row_id
        message = _replace_var(row_id, row.message)
        log.var('row_id', row_id)
        log.var('message', message)

        cmd_line = _replace_var(row_id, row.cmd_line)
        expected_return_code = int(row.return_code)
        expected_return_type = row.return_type
        return_filter = _replace_var(row_id, row.return_filter)
        save_var_name = row.var_name
        log.var('cmd_line', cmd_line)
        log.var('expected_return_code', expected_return_code)
        log.var('expected_return_type', expected_return_type)
        log.var('return_filter', return_filter)
        log.var('save_var_name', save_var_name)

        return_code, result = execute_cmd(cmd_line, remove_white_char='\n')
        log.var('return_code', return_code)
        log.var('result', result)

        if expected_return_code == return_code:
            if return_filter != NULL_VALUE and save_var_name != NULL_VALUE:
                m = re.match(r'%s' % return_filter, result)

                if m:
                    value = m.group(1)
                    # 保存筛选结果到暂存变量
                    if expected_return_type == ReturnType.INT:
                        exec('_var_tmp_storage_area[\'%s\'] = %d' % (save_var_name, int(value)), globals())
                    else:
                        exec('_var_tmp_storage_area[\'%s\'] = \'%s\'' % (save_var_name, m.group(1)), globals())
                    log.info(_output_message_builder(row_id, message, True))
                else:
                    log.error(cmd_line)
                    log.info(_output_message_builder(row_id, message, False))
                    raise HappyPyException('在执行结果上匹配过滤器，匹配内容为空')
            else:
                if save_var_name != NULL_VALUE:
                    _var_tmp_storage_area[save_var_name] = result

                log.info(_output_message_builder(row_id, message, True))
        else:
            log.error(cmd_line)
            log.info(_output_message_builder(row_id, message, False))
            raise HappyPyException('执行命令返回代码（%s）与预期（%s）不符' % (return_code, expected_return_code))

        log.exit_func(fn_name)

    @staticmethod
    def statement_handler(row: CsvRow):
        fn_name = inspect.stack()[0][3]
        log.enter_func(fn_name)

        log.var('row', row)

        row_id = row.row_id
        message = _replace_var(row_id, row.message)
        log.var('row_id', row_id)
        log.var('message', message)

        cmd_line = _replace_var(row_id, row.cmd_line)
        return_filter = _replace_var(row_id, row.return_filter)
        save_var_name = row.var_name
        expected_return_type = row.return_type
        is_expected_return_int_type = expected_return_type == ReturnType.INT
        expected_return_value = int(row.default_value) if expected_return_type == ReturnType.INT else row.default_value
        log.var('cmd_line', cmd_line)
        log.var('return_filter', return_filter)
        log.var('save_var_name', save_var_name)
        log.var('expected_return_type', expected_return_type)
        log.var('is_expected_return_int_type', is_expected_return_int_type)
        log.var('expected_return_value', expected_return_value)

        if expected_return_type == ReturnType.INT:
            statement = 'tmp = int(%s)' % cmd_line
        else:
            statement = 'tmp = %s' % cmd_line

        log.var('statement', statement)

        try:
            exec(statement, locals())
            result = locals().get('tmp')
            result = int(result) if is_expected_return_int_type else str(result)

            if expected_return_value == result:
                log.info(_output_message_builder(row_id, message, True))

                # 保存执行结果到暂存变量
                if save_var_name != NULL_VALUE:
                    _var_tmp_storage_area[save_var_name] = result
            else:
                log.info(_output_message_builder(row_id, message, False))
                raise HappyPyException('返回值（%s）与预期（%s）不符' % (result, expected_return_value))
        except Exception as e:
            log.error(statement)
            log.critical(e)
            raise HappyPyException(_output_message_builder(row_id, message, False))

        log.exit_func(fn_name)


# 列数量
COL_SIZE = len(ColInfo)
# 每列对应的值校验函数
COL_VALIDATE_X_MAP = {
    ColInfo.RowID: ColValidator.validate_row_id,
    ColInfo.ModeType: ColValidator.validate_mode_type,
    ColInfo.CmdLine: ColValidator.validate_cmd_line,
    ColInfo.ReturnCode: ColValidator.validate_return_code,
    ColInfo.ReturnType: ColValidator.validate_return_type,
    ColInfo.DefaultValue: ColValidator.validate_default_value,
    ColInfo.ReturnFilter: ColValidator.validate_return_filter,
    ColInfo.VarName: ColValidator.validate_var_name,
    ColInfo.Message: ColValidator.validate_message,
}
# 每种模式的行逻辑校验函数
ROW_VALIDATE_X_MAP = {
    ModeType.CONST: RowValidator.validate_const_row,
    ModeType.MESSAGE: RowValidator.validate_message_row,
    ModeType.ENV: RowValidator.validate_env_row,
    ModeType.CMD: RowValidator.validate_cmd_row,
    ModeType.STATEMENT: RowValidator.validate_statement_row,
}
# 每种模式的行处理函数
ROW_HANDLER_MAP = {
    ModeType.CONST: RowHandler.const_handler,
    ModeType.MESSAGE: RowHandler.message_handler,
    ModeType.ENV: RowHandler.env_handler,
    ModeType.CMD: RowHandler.cmd_handler,
    ModeType.STATEMENT: RowHandler.statement_handler,
}


def to_csv_row_obj(row: list) -> CsvRow:
    fn_name = inspect.stack()[0][3]
    log.enter_func(fn_name)

    log.var('row', row)

    if len(row) != COL_SIZE:
        raise HappyPyException('数组%s的数量不正确，应该有%d个元素' % (row, COL_SIZE))

    n = 0
    for c in ColInfo:
        assert c in COL_VALIDATE_X_MAP
        # 获取校验函数
        col_validate_fun = COL_VALIDATE_X_MAP.get(c)
        # 调用列对应的校验函数
        col_validate_fun(row[n])
        n += 1

    row_id: str = row[0]
    mode_type = ModeType[row[1]]
    cmd_line = row[2]
    return_code = row[3]
    return_type = ReturnType[row[4]]
    default_value = row[5]
    return_filter = row[6]
    var_name = row[7]
    message = row[8]

    csv_row = CsvRow(row_id, mode_type, cmd_line, return_code, return_type,
                     default_value, return_filter, var_name, message)
    row_validate_fun = ROW_VALIDATE_X_MAP.get(mode_type)

    if row_validate_fun:
        row_validate_fun(csv_row)
    else:
        msg = '第%d行->%s：无效值"%s"，可选值为CONST_VAR、VAR、ENV和CMD' % (line_number, ColInfo.ModeType.value, row[1])
        raise HappyPyException(msg)

    log.exit_func(fn_name)
    return csv_row


def raining(csv_file: str):
    global line_number

    try:
        with open(csv_file, encoding='UTF-8') as f:
            try:
                reader = csv.reader(f)

                for row in reader:
                    line_number += 1

                    # 跳过标题行
                    if line_number == 1:
                        continue

                    row_obj = to_csv_row_obj(row)
                    handler = ROW_HANDLER_MAP.get(row_obj.mode_type)
                    handler(row_obj)
            except csv.Error as e:
                msg = '解析CSV文件行时出现错误\n'
                msg += '%s,%d行: %s' % (csv_file, reader.line_num, e)
                raise HappyPyException(msg)
    except FileExistsError as e:
        msg = '读取文件错误：%s：%s' % (csv_file, e)
        log.error(msg)
        raise HappyPyException(msg)
    except FileNotFoundError:
        msg = '文件不存在：%s' % csv_file
        log.error('文件不存在：%s' % csv_file)
        raise HappyPyException(msg)


def main():
    global log
    parser = argparse.ArgumentParser(prog='rain_shell_scripter',
                                     description='用Python加持Linux Shell脚本，编写CSV文件即可完美解决脚本中的返回值、数值运算、错误处理、流程控制难题~',
                                     usage='%(prog)s -f|-l')

    parser.add_argument('-f',
                        '--file',
                        help='CSV文件',
                        required=True,
                        action='store',
                        dest='csv_file')

    parser.add_argument('-l',
                        '--log-level',
                        help='日志级别，CRITICAL|ERROR|WARNING|INFO|DEBUG|TRACE，默认等级3（INFO）',
                        type=int,
                        choices=HappyLogLevel.get_list(),
                        default=HappyLogLevel.INFO.value,
                        required=False,
                        dest='log_level')

    parser.add_argument('-v',
                        '--version',
                        help='显示版本信息',
                        action='version',
                        version='%(prog)s/v' + __version__)

    args = parser.parse_args()
    log.set_level(args.log_level)

    # noinspection PyUnusedLocal
    def sigint_handler(sig, frame):
        log.info('\n\n收到 Ctrl+C 信号，退出......')

    # 前台运行收到 CTRL+C 信号，直接退出。
    signal.signal(signal.SIGINT, sigint_handler)

    try:
        raining(args.csv_file)
        log.debug('变量暂存区：\n' + dict_to_pretty_json(_var_tmp_storage_area))
    except HappyPyException as e:
        log.error(e)
        exit(1)


if __name__ == '__main__':
    main()
