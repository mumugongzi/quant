# 验证A股技术指标是否有效
# 数据
* [A股日线数据下载](https://www.yucezhe.com/product/data/trading)

# 使用
* 环境初始化
```bash
sh build/init_env.sh
```
* 将下载下来的数据直接放到项目目录下, 然后在src/common/config.py中设置好指数和股票数据路径
* 运行验证程序

# Python版本
* Python 3.6.6

# 小贴士
* 预测者网提供的万科互数据(sz000002)在1993-10-17之前的周六有交易数据, 原因目前不详


