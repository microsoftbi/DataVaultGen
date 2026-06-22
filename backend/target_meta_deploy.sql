/*
 ============================================================================
 DWH-Generator META 数据库部署脚本
 在 SQL Server 中执行此脚本创建 META 配置数据库。
 ============================================================================
*/

-- 创建数据库（如不存在）
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'META')
BEGIN
    CREATE DATABASE [META]
END
GO

USE [META]
GO

-- ===========================================================================
-- 1. 表定义
-- ===========================================================================

-- 对象列表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'GEN_LIST')
BEGIN
    CREATE TABLE [dbo].[GEN_LIST] (
        [ID] INT IDENTITY(1,1) PRIMARY KEY,
        [TABLE_CATALOG] NVARCHAR(128) NULL,
        [TABLE_NAME] NVARCHAR(128) NOT NULL,
        [SCHEMA_NAME] NVARCHAR(128) DEFAULT 'dbo',
        [IS_GEN] BIT DEFAULT 1,
        [IS_FULL_LOAD] BIT DEFAULT 0,
        [CREATED_AT] DATETIME DEFAULT GETDATE(),
        CONSTRAINT [UQ_GEN_LIST] UNIQUE ([TABLE_CATALOG], [TABLE_NAME])
    )
END
GO

-- 列属性元数据
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ATTRIBUTE')
BEGIN
    CREATE TABLE [dbo].[ATTRIBUTE] (
        [ID] INT IDENTITY(1,1) PRIMARY KEY,
        [TABLE_CATALOG] NVARCHAR(128) NULL,
        [TABLE_NAME] NVARCHAR(128) NOT NULL,
        [COLUMN_NAME] NVARCHAR(128) NOT NULL,
        [DATA_TYPE] NVARCHAR(128) NULL,
        [CHARACTER_MAXIMUM_LENGTH] INT NULL,
        [NUMERIC_PRECISION] TINYINT NULL,
        [NUMERIC_SCALE] INT NULL,
        [IS_BK] BIT DEFAULT 0,
        [IS_PK] BIT DEFAULT 0,
        [IS_DI] BIT DEFAULT 0,
        [CREATED_AT] DATETIME DEFAULT GETDATE()
    )
END
GO

-- 登记源
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'RECORD_SOURCE')
BEGIN
    CREATE TABLE [dbo].[RECORD_SOURCE] (
        [ID] INT IDENTITY(1,1) PRIMARY KEY,
        [DATABASE_NAME] NVARCHAR(128) NULL,
        [RECORD_SOURCE_NAME] NVARCHAR(128) NOT NULL
    )
END
GO

-- 数据库连接配置
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'CONNECTION_CONFIG')
BEGIN
    CREATE TABLE [dbo].[CONNECTION_CONFIG] (
        [ID] INT IDENTITY(1,1) PRIMARY KEY,
        [NAME] NVARCHAR(128) NOT NULL,
        [DB_TYPE] NVARCHAR(32) DEFAULT 'sqlserver',
        [HOST] NVARCHAR(255) NULL,
        [PORT] INT DEFAULT 1433,
        [DATABASE_NAME] NVARCHAR(128) NULL,
        [USERNAME] NVARCHAR(128) NULL,
        [PASSWORD_ENCRYPTED] NVARCHAR(MAX) NULL,
        [IS_META] BIT DEFAULT 0,
        [IS_SOURCE] BIT DEFAULT 0,
        [IS_TARGET] BIT DEFAULT 0,
        [CREATED_AT] DATETIME DEFAULT GETDATE()
    )
END
GO

-- 配置参数
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'CONFIGURATION')
BEGIN
    CREATE TABLE [dbo].[CONFIGURATION] (
        [ID] INT IDENTITY(1,1) PRIMARY KEY,
        [CONFIG_NAME] NVARCHAR(128) NOT NULL UNIQUE,
        [CONFIG_VALUE] NVARCHAR(MAX) NULL,
        [DESCRIPTION] NVARCHAR(500) NULL
    )
END
GO

-- 执行日志
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'EXECUTION_LOG')
BEGIN
    CREATE TABLE [dbo].[EXECUTION_LOG] (
        [ID] INT IDENTITY(1,1) PRIMARY KEY,
        [LOG_SOURCE] NVARCHAR(255) NULL,
        [LOG_TYPE] CHAR(1) DEFAULT 'N',
        [MESSAGE] NVARCHAR(MAX) NULL,
        [CREATED_AT] DATETIME DEFAULT GETDATE()
    )
END
GO

-- ===========================================================================
-- 2. 存储过程
-- ===========================================================================

-- USP_INIT_LIST: 将 ATTRIBUTE 中的表初始化到 GEN_LIST
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'USP_INIT_LIST')
    DROP PROCEDURE [dbo].[USP_INIT_LIST]
GO

CREATE PROCEDURE [dbo].[USP_INIT_LIST]
AS
BEGIN
    SET NOCOUNT ON

    INSERT INTO [dbo].[GEN_LIST] ([TABLE_CATALOG], [TABLE_NAME], [SCHEMA_NAME])
    SELECT DISTINCT
        NULL AS [TABLE_CATALOG],
        [TABLE_NAME],
        'dbo' AS [SCHEMA_NAME]
    FROM [dbo].[ATTRIBUTE]
    WHERE [TABLE_NAME] NOT IN (
        SELECT [TABLE_NAME] FROM [dbo].[GEN_LIST]
    )
END
GO

-- USP_WRITELOG: 写入执行日志
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'USP_WRITELOG')
    DROP PROCEDURE [dbo].[USP_WRITELOG]
GO

CREATE PROCEDURE [dbo].[USP_WRITELOG]
    @MESSAGE NVARCHAR(MAX),
    @LOG_SOURCE NVARCHAR(255) = NULL,
    @LOG_TYPE CHAR(1) = 'N'
AS
BEGIN
    SET NOCOUNT ON

    INSERT INTO [dbo].[EXECUTION_LOG] ([LOG_SOURCE], [LOG_TYPE], [MESSAGE], [CREATED_AT])
    VALUES (@LOG_SOURCE, @LOG_TYPE, @MESSAGE, GETDATE())
END
GO

-- ===========================================================================
-- 3. 视图
-- ===========================================================================

-- V_ATTRIBUTE: 字段配置综合视图（兼容原始项目命名）
IF EXISTS (SELECT * FROM sys.views WHERE name = 'V_ATTRIBUTE')
    DROP VIEW [dbo].[V_ATTRIBUTE]
GO

CREATE VIEW [dbo].[V_ATTRIBUTE]
AS
SELECT
    A.[ID],
    A.[TABLE_CATALOG],
    A.[TABLE_NAME],
    A.[COLUMN_NAME],
    A.[DATA_TYPE],
    A.[CHARACTER_MAXIMUM_LENGTH],
    A.[NUMERIC_PRECISION],
    A.[NUMERIC_SCALE],
    ISNULL(RS.[RECORD_SOURCE_NAME], 'dbo') AS [RECORDSOURCE],
    A.[IS_BK] AS [BK],
    A.[IS_PK] AS [PK],
    A.[IS_DI] AS [DI],
    ISNULL(G.[IS_FULL_LOAD], 0) AS [IS_FULLLOAD]
FROM [dbo].[ATTRIBUTE] A
LEFT JOIN [dbo].[RECORD_SOURCE] RS ON A.[TABLE_CATALOG] = RS.[DATABASE_NAME]
INNER JOIN [dbo].[GEN_LIST] G ON A.[TABLE_NAME] = G.[TABLE_NAME]
WHERE G.[IS_GEN] = 1
GO

-- ===========================================================================
-- 4. 初始化数据
-- ===========================================================================

IF NOT EXISTS (SELECT * FROM [dbo].[CONFIGURATION] WHERE [CONFIG_NAME] = 'HASHDUMMY')
BEGIN
    INSERT INTO [dbo].[CONFIGURATION] ([CONFIG_NAME], [CONFIG_VALUE], [DESCRIPTION])
    VALUES ('HASHDUMMY', '@IAMHUSKIES@', 'Hash key 计算时字段间的填充串')
END
GO

IF NOT EXISTS (SELECT * FROM [dbo].[CONFIGURATION] WHERE [CONFIG_NAME] = 'PSA_DB')
BEGIN
    INSERT INTO [dbo].[CONFIGURATION] ([CONFIG_NAME], [CONFIG_VALUE], [DESCRIPTION])
    VALUES ('PSA_DB', 'STAGE', 'PSA 层数据库名称')
END
GO

PRINT 'META 数据库部署完成'
GO