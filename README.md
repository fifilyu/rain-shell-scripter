# rain-shell-scripter

用Python加持Linux Shell脚本，编写CSV文件即可完美解决脚本中的返回值、数值运算、错误处理、流程控制难题~

## 介绍

工作生活中存在编写脚本的情况，用Python写代码太重，写脚本可读性和控制力度又太差。

比如，在Shell脚本中，计算 `1+1` 的情况，上下行存在逻辑控制流的时候。

`rain-shell-scripter` 让我从Shell语法、格式中解放出来，仅需要编写CSV规则文件，就能满足场景需求。

最近，在忙Jenkins自动构建，需要编写大量脚本。所以，干脆写了 `rain-shell-scripter` 来解决类似需求。

## 环境要求

* Python 3.8.0及以上版本

## 安装

    pip3 install rain-shell-scripter

## 使用

### 获取规则文件示例

    git clone https://github.com/fifilyu/rain-shell-scripter.git

### 运行

    $ cd rain-shell-scripter
    $ rain_shell_scripter -f examples/hello.csv 
    
    2020-09-29 14:53:40 22250 [INFO] 编号：B00 -> 设置项目名称...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B01 -> 开始......构建项目——hello...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B02 -> 获取当前工作目录...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B03 -> 设置环境变量"WORK_DIR"...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B04 -> 模拟->Maven构建项目——hello...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B05 -> 模拟->确认构建后存在target文件（JAR包）...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B06 -> 模拟->获取target文件名称...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B08 -> 模拟->本地环境-生成JAR包的哈希值...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B09 -> 模拟->目标环境-生成JAR包的哈希值...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B10 -> 期望的哈希值...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B11 -> 模拟->对比JAR包的哈希值...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B12 -> 复制文件测试1...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B13 -> 复制文件测试2...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B14 -> 删除文件...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B15 -> 复制文件测试2...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B16 -> 模拟->目标环境-删除构建目录...[ OK ]
    2020-09-29 14:53:40 22250 [INFO] 编号：B17 -> 结束......构建项目——hello...[ OK 

或者以调试模式运行：

    $ cd rain-shell-scripter
    $ rain_shell_scripter -f examples/hello.csv  -l 5

    2020-09-29 14:54:14 22280 [TRACE] Enter function: to_csv_row_obj
    2020-09-29 14:54:14 22280 [TRACE] row=['B00', 'CONST', 'NULL', 'NULL', 'STR', 'hello', 'NULL', 'PROJECT', '设置项目名称']
    2020-09-29 14:54:14 22280 [TRACE] Exit function: to_csv_row_obj
    2020-09-29 14:54:14 22280 [TRACE] Enter function: const_handler
    2020-09-29 14:54:14 22280 [TRACE] row=<__main__.CsvRow object at 0x7fdee148feb0>
    2020-09-29 14:54:14 22280 [TRACE] row_id=B00
    2020-09-29 14:54:14 22280 [TRACE] message=设置项目名称
    2020-09-29 14:54:14 22280 [TRACE] var_name=PROJECT
    2020-09-29 14:54:14 22280 [TRACE] var_value=hello
    ...
    ...
    ...
    2020-09-29 14:54:14 22280 [INFO] 编号：B16 -> 模拟->目标环境-删除构建目录...[ OK ]
    2020-09-29 14:54:14 22280 [TRACE] Exit function: expr_handler
    2020-09-29 14:54:14 22280 [TRACE] Enter function: to_csv_row_obj
    2020-09-29 14:54:14 22280 [TRACE] row=['B17', 'MESSAGE', 'NULL', 'NULL', 'NULL', 'NULL', 'NULL', 'NULL', '结束......构建项目——${PROJECT}']
    2020-09-29 14:54:14 22280 [TRACE] Exit function: to_csv_row_obj
    2020-09-29 14:54:14 22280 [TRACE] Enter function: message_handler
    2020-09-29 14:54:14 22280 [TRACE] row=<__main__.CsvRow object at 0x7fdee148f940>
    2020-09-29 14:54:14 22280 [TRACE] row_id=B17
    2020-09-29 14:54:14 22280 [TRACE] message=结束......构建项目——hello
    2020-09-29 14:54:14 22280 [INFO] 编号：B17 -> 结束......构建项目——hello...[ OK ]
    2020-09-29 14:54:14 22280 [TRACE] Exit function: message_handler
    2020-09-29 14:54:14 22280 [DEBUG] 变量暂存区：
    {
        "PROJECT": "hello",
        "expected_hash": "e0aa021e21dddbd6d8cecec71e9cf564",
        "local_hash": "e0aa021e21dddbd6d8cecec71e9cf564",
        "pwd": "/home/lyuqiang/workspace/rain-shell-scripter",
        "remote_hash": "e0aa021e21dddbd6d8cecec71e9cf564",
        "target_file": "hello-1.0.0.jar"
    }




`-l 5` 表示最高调试模式，会打印更多的日志。

## CSV文件编写规则

### 示例：examples/hello.csv

```csv
编号,模式,表达式,返回代码,返回类型,返回值,过滤器,变量名,提示信息
B00,CONST,NULL,NULL,STR,hello,NULL,PROJECT,设置项目名称
B01,MESSAGE,NULL,NULL,NULL,NULL,NULL,NULL,开始......构建项目——${PROJECT}
B02,RUN,pwd,0,STR,NULL,NULL,pwd,获取当前工作目录
B03,ENV,NULL,NULL,NULL,${pwd},NULL,JAVA_HOME,"设置环境变量""WORK_DIR"""
B04,RUN,mkdir -p target && echo -n OK > target/hello-1.0.0.jar,0,NULL,NULL,NULL,NULL,模拟->Maven构建项目——${PROJECT}
B05,RUN,ls target/hello-*.jar,0,NULL,NULL,NULL,NULL,模拟->确认构建后存在target文件（JAR包）
B06,RUN,basename target/hello-*.jar,0,STR,NULL,NULL,target_file,模拟->获取target文件名称
B08,RUN,md5sum target/${target_file},0,NULL,NULL,^([\d\w]+) .*$,local_hash,模拟->本地环境-生成JAR包的哈希值
B09,RUN,echo ${local_hash},0,NULL,NULL,NULL,remote_hash,模拟->目标环境-生成JAR包的哈希值
B10,CONST,NULL,NULL,STR,e0aa021e21dddbd6d8cecec71e9cf564,NULL,expected_hash,期望的哈希值
B11,STATEMENT,'${local_hash}' == '${expected_hash}',NULL,INT,1,NULL,NULL,模拟->对比JAR包的哈希值
B12,COPY,target/hello-1.0.0.jar target/hello-1.0.0.zip,NULL,NULL,NULL,NULL,NULL,复制文件测试1
B13,COPY,target target1,NULL,NULL,NULL,NULL,NULL,复制文件测试2
B14,RUN,rm -f target1/hello-1.0.0.jar,0,NULL,NULL,NULL,NULL,删除文件
B15,COPY,target/hello-1.0.0.jar target1/,NULL,NULL,NULL,NULL,NULL,复制文件测试2
B16,RUN,rm -rf target/ target1/,0,NULL,NULL,NULL,NULL,模拟->目标环境-删除构建目录
B17,MESSAGE,NULL,NULL,NULL,NULL,NULL,NULL,结束......构建项目——${PROJECT}
```

### 规则

__在规则文件不完善的情况下，可以用 `-f` 执行规则，程序会提示每行或者每列应该是哪种类型的值。__


#### 公共规则

* 不需要填写或定义的值，设置为 `NULL`；
* `${xxx}` 格式的内容会被临时变量堆栈或环境变量中的值替换。比如，在我的Linux系统中， `${USER}` 会被替换为环境变量中的 `fifilyu`；
* 区分大小写；
* 标题行必须保留（`编号,模式,命令,返回代码,返回类型,返回值,过滤器,变量名,提示信息`），程序会跳过第一行；

#### 列规则

1. `编号`：任意大小写字母+数字；
2. `模式` 可选项：
   * RUN：执行Shell命令
   * ENV：设置脚本环境变量，运行期间有效；
   * MESSAGE：打印提示消息到标准输出（如屏幕）；
   * STATEMENT：执行单行Python代码，用来实现if语句；
   * CONST：常量
   * COPY：复制文件或目录
3. `返回代码` 只能是整数， `0` 表示命令执行成功，非 `0`（比如 `1`）表示命令执行失败；
4. `返回类型` 可选项：
   * INT：数字
   * STR：字符串
5. `返回值`：`RUN`、`ENV`、`CONST`模式下才需要设置，默认为NULL即可；
6. `过滤器`：Python支持的正则表达式规则，需要用一对 `()` 捕获一个值。比如，用 `^([\d\w]+) .*$` 正则规则捕获 `effab107db895c213be26c242e68a722 test.txt` 中的 `effab107db895c213be26c242e68a722`；
7. `变量名`：各种模式下，将执行命令或正则匹配的结果保存到指定的变量，用于规则后面的逻辑；
8. `提示信息`：仅打印信息内容。
