# 系统说明

## 摘要
这个系统的目的是，辅助设计数据仓库，数据仓库遵从Data Vault的设计方式。

系统从另外一个老系统转换而来：https://github.com/microsoftbi/DWH-Generator

## 假设条件
假设有一个OLTP数据库：TEST_STORE
我们的数据仓库包含两个库(这两个库需要手动创建)：
-   STAGE
-   CORE