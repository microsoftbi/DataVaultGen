# 系统说明

## 摘要
这个系统的目的是，辅助设计数据仓库，数据仓库遵从Data Vault的设计方式。

系统从另外一个老系统转换而来：https://github.com/microsoftbi/DWH-Generator

## 假设条件
假设有一个OLTP数据库：TEST_STORE

OLTP库里包含有我们数据仓库需要读取的表。

这个工具会读取这个OLTP库的表和字段的信息，做相应的配置，然后自动生成以下代码：
- STAGE库里的表的建表脚本
- STAGE库里的存储过程，用于把表从OLTP库加载进STAGE表中。这里假设读取用的是全量加载。
- STAGE库里针对表的视图，这些视图会生成hash key的信息，用于后期增量逻辑的处理。
- CORE库里表的建表脚本。
- CORE库里的存储过程，用于把STAGE库里的数据加载到CORE库中。

我们的数据仓库包含两个库(这两个库需要手动创建)：
-   STAGE
-   CORE
  
STAGE库和CORE库手动建立好之后，可以启动该系统。

后端的启动：

···
cd backend
python main.py
···

前端的启动：

···
cd frontend
npm run dev
···