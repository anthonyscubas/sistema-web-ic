-- Ejecutar sobre la base de datos SQL Server existente antes de publicar la nueva versión.
-- No elimina datos ni columnas anteriores. Realizar copia de seguridad primero.
IF OBJECT_ID(N'dbo.encuestas_internas', N'U') IS NOT NULL AND COL_LENGTH('dbo.encuestas_internas', 'comunica_status_tiempo') IS NULL
    ALTER TABLE dbo.encuestas_internas ADD [comunica_status_tiempo] INT NULL;
GO
IF OBJECT_ID(N'dbo.encuestas_internas', N'U') IS NOT NULL AND COL_LENGTH('dbo.encuestas_internas', 'registra_inconsistencias') IS NULL
    ALTER TABLE dbo.encuestas_internas ADD [registra_inconsistencias] INT NULL;
GO
IF OBJECT_ID(N'dbo.encuestas_internas', N'U') IS NOT NULL AND COL_LENGTH('dbo.encuestas_internas', 'propone_soluciones') IS NULL
    ALTER TABLE dbo.encuestas_internas ADD [propone_soluciones] INT NULL;
GO
IF OBJECT_ID(N'dbo.encuestas_alicorp', N'U') IS NOT NULL AND COL_LENGTH('dbo.encuestas_alicorp', 'registra_inconsistencias') IS NULL
    ALTER TABLE dbo.encuestas_alicorp ADD [registra_inconsistencias] INT NULL;
GO
