
SET XACT_ABORT ON;
BEGIN TRY
 BEGIN TRAN;
 IF OBJECT_ID(N'dbo.encuestas_internas', N'U') IS NOT NULL
 BEGIN
  IF OBJECT_ID(N'dbo.respaldo_limpieza_encuestas_internas_20261012', N'U') IS NOT NULL
    THROW 51001, 'Ya existe el respaldo de encuestas_internas; revise antes de volver a ejecutar.', 1;
  SELECT * INTO dbo.respaldo_limpieza_encuestas_internas_20261012 FROM dbo.encuestas_internas;
  PRINT 'Respaldo generado para encuestas_internas';
  IF COL_LENGTH('dbo.encuestas_internas', 'cumplimiento') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_internas_cumplimiento SYSNAME;
   SELECT @constraint_encuestas_internas_cumplimiento = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_internas') AND sc.name='cumplimiento';
   IF @constraint_encuestas_internas_cumplimiento IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_internas DROP CONSTRAINT [' + @constraint_encuestas_internas_cumplimiento + ']');
   ALTER TABLE dbo.encuestas_internas DROP COLUMN [cumplimiento];
  END;
  IF COL_LENGTH('dbo.encuestas_internas', 'calidad') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_internas_calidad SYSNAME;
   SELECT @constraint_encuestas_internas_calidad = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_internas') AND sc.name='calidad';
   IF @constraint_encuestas_internas_calidad IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_internas DROP CONSTRAINT [' + @constraint_encuestas_internas_calidad + ']');
   ALTER TABLE dbo.encuestas_internas DROP COLUMN [calidad];
  END;
  IF COL_LENGTH('dbo.encuestas_internas', 'autonomia') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_internas_autonomia SYSNAME;
   SELECT @constraint_encuestas_internas_autonomia = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_internas') AND sc.name='autonomia';
   IF @constraint_encuestas_internas_autonomia IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_internas DROP CONSTRAINT [' + @constraint_encuestas_internas_autonomia + ']');
   ALTER TABLE dbo.encuestas_internas DROP COLUMN [autonomia];
  END;
  IF COL_LENGTH('dbo.encuestas_internas', 'prevencion_comunicacion') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_internas_prevencion_comunicacion SYSNAME;
   SELECT @constraint_encuestas_internas_prevencion_comunicacion = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_internas') AND sc.name='prevencion_comunicacion';
   IF @constraint_encuestas_internas_prevencion_comunicacion IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_internas DROP CONSTRAINT [' + @constraint_encuestas_internas_prevencion_comunicacion + ']');
   ALTER TABLE dbo.encuestas_internas DROP COLUMN [prevencion_comunicacion];
  END;
  IF COL_LENGTH('dbo.encuestas_internas', 'mejora_continua') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_internas_mejora_continua SYSNAME;
   SELECT @constraint_encuestas_internas_mejora_continua = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_internas') AND sc.name='mejora_continua';
   IF @constraint_encuestas_internas_mejora_continua IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_internas DROP CONSTRAINT [' + @constraint_encuestas_internas_mejora_continua + ']');
   ALTER TABLE dbo.encuestas_internas DROP COLUMN [mejora_continua];
  END;
  IF COL_LENGTH('dbo.encuestas_internas', 'reportes_bi') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_internas_reportes_bi SYSNAME;
   SELECT @constraint_encuestas_internas_reportes_bi = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_internas') AND sc.name='reportes_bi';
   IF @constraint_encuestas_internas_reportes_bi IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_internas DROP CONSTRAINT [' + @constraint_encuestas_internas_reportes_bi + ']');
   ALTER TABLE dbo.encuestas_internas DROP COLUMN [reportes_bi];
  END;
  IF COL_LENGTH('dbo.encuestas_internas', 'errores_front') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_internas_errores_front SYSNAME;
   SELECT @constraint_encuestas_internas_errores_front = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_internas') AND sc.name='errores_front';
   IF @constraint_encuestas_internas_errores_front IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_internas DROP CONSTRAINT [' + @constraint_encuestas_internas_errores_front + ']');
   ALTER TABLE dbo.encuestas_internas DROP COLUMN [errores_front];
  END;
  IF COL_LENGTH('dbo.encuestas_internas', 'entregables_solicitados') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_internas_entregables_solicitados SYSNAME;
   SELECT @constraint_encuestas_internas_entregables_solicitados = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_internas') AND sc.name='entregables_solicitados';
   IF @constraint_encuestas_internas_entregables_solicitados IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_internas DROP CONSTRAINT [' + @constraint_encuestas_internas_entregables_solicitados + ']');
   ALTER TABLE dbo.encuestas_internas DROP COLUMN [entregables_solicitados];
  END;
  IF COL_LENGTH('dbo.encuestas_internas', 'entregables_plazo') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_internas_entregables_plazo SYSNAME;
   SELECT @constraint_encuestas_internas_entregables_plazo = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_internas') AND sc.name='entregables_plazo';
   IF @constraint_encuestas_internas_entregables_plazo IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_internas DROP CONSTRAINT [' + @constraint_encuestas_internas_entregables_plazo + ']');
   ALTER TABLE dbo.encuestas_internas DROP COLUMN [entregables_plazo];
  END;
  IF COL_LENGTH('dbo.encuestas_internas', 'riesgos') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_internas_riesgos SYSNAME;
   SELECT @constraint_encuestas_internas_riesgos = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_internas') AND sc.name='riesgos';
   IF @constraint_encuestas_internas_riesgos IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_internas DROP CONSTRAINT [' + @constraint_encuestas_internas_riesgos + ']');
   ALTER TABLE dbo.encuestas_internas DROP COLUMN [riesgos];
  END;
  IF COL_LENGTH('dbo.encuestas_internas', 'riesgos_oportunos') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_internas_riesgos_oportunos SYSNAME;
   SELECT @constraint_encuestas_internas_riesgos_oportunos = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_internas') AND sc.name='riesgos_oportunos';
   IF @constraint_encuestas_internas_riesgos_oportunos IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_internas DROP CONSTRAINT [' + @constraint_encuestas_internas_riesgos_oportunos + ']');
   ALTER TABLE dbo.encuestas_internas DROP COLUMN [riesgos_oportunos];
  END;
  IF COL_LENGTH('dbo.encuestas_internas', 'propuestas') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_internas_propuestas SYSNAME;
   SELECT @constraint_encuestas_internas_propuestas = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_internas') AND sc.name='propuestas';
   IF @constraint_encuestas_internas_propuestas IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_internas DROP CONSTRAINT [' + @constraint_encuestas_internas_propuestas + ']');
   ALTER TABLE dbo.encuestas_internas DROP COLUMN [propuestas];
  END;
  IF COL_LENGTH('dbo.encuestas_internas', 'propuestas_aprobadas') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_internas_propuestas_aprobadas SYSNAME;
   SELECT @constraint_encuestas_internas_propuestas_aprobadas = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_internas') AND sc.name='propuestas_aprobadas';
   IF @constraint_encuestas_internas_propuestas_aprobadas IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_internas DROP CONSTRAINT [' + @constraint_encuestas_internas_propuestas_aprobadas + ']');
   ALTER TABLE dbo.encuestas_internas DROP COLUMN [propuestas_aprobadas];
  END;
 END;
 IF OBJECT_ID(N'dbo.encuestas_alicorp', N'U') IS NOT NULL
 BEGIN
  IF OBJECT_ID(N'dbo.respaldo_limpieza_encuestas_alicorp_20261012', N'U') IS NOT NULL
    THROW 51001, 'Ya existe el respaldo de encuestas_alicorp; revise antes de volver a ejecutar.', 1;
  SELECT * INTO dbo.respaldo_limpieza_encuestas_alicorp_20261012 FROM dbo.encuestas_alicorp;
  PRINT 'Respaldo generado para encuestas_alicorp';
  IF COL_LENGTH('dbo.encuestas_alicorp', 'solicita_datos_tiempo') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_alicorp_solicita_datos_tiempo SYSNAME;
   SELECT @constraint_encuestas_alicorp_solicita_datos_tiempo = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_alicorp') AND sc.name='solicita_datos_tiempo';
   IF @constraint_encuestas_alicorp_solicita_datos_tiempo IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_alicorp DROP CONSTRAINT [' + @constraint_encuestas_alicorp_solicita_datos_tiempo + ']');
   ALTER TABLE dbo.encuestas_alicorp DROP COLUMN [solicita_datos_tiempo];
  END;
  IF COL_LENGTH('dbo.encuestas_alicorp', 'envia_validar_plazo') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_alicorp_envia_validar_plazo SYSNAME;
   SELECT @constraint_encuestas_alicorp_envia_validar_plazo = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_alicorp') AND sc.name='envia_validar_plazo';
   IF @constraint_encuestas_alicorp_envia_validar_plazo IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_alicorp DROP CONSTRAINT [' + @constraint_encuestas_alicorp_envia_validar_plazo + ']');
   ALTER TABLE dbo.encuestas_alicorp DROP COLUMN [envia_validar_plazo];
  END;
  IF COL_LENGTH('dbo.encuestas_alicorp', 'capacita_actualizaciones') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_alicorp_capacita_actualizaciones SYSNAME;
   SELECT @constraint_encuestas_alicorp_capacita_actualizaciones = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_alicorp') AND sc.name='capacita_actualizaciones';
   IF @constraint_encuestas_alicorp_capacita_actualizaciones IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_alicorp DROP CONSTRAINT [' + @constraint_encuestas_alicorp_capacita_actualizaciones + ']');
   ALTER TABLE dbo.encuestas_alicorp DROP COLUMN [capacita_actualizaciones];
  END;
  IF COL_LENGTH('dbo.encuestas_alicorp', 'calidad') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_alicorp_calidad SYSNAME;
   SELECT @constraint_encuestas_alicorp_calidad = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_alicorp') AND sc.name='calidad';
   IF @constraint_encuestas_alicorp_calidad IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_alicorp DROP CONSTRAINT [' + @constraint_encuestas_alicorp_calidad + ']');
   ALTER TABLE dbo.encuestas_alicorp DROP COLUMN [calidad];
  END;
  IF COL_LENGTH('dbo.encuestas_alicorp', 'cumplimiento') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_alicorp_cumplimiento SYSNAME;
   SELECT @constraint_encuestas_alicorp_cumplimiento = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_alicorp') AND sc.name='cumplimiento';
   IF @constraint_encuestas_alicorp_cumplimiento IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_alicorp DROP CONSTRAINT [' + @constraint_encuestas_alicorp_cumplimiento + ']');
   ALTER TABLE dbo.encuestas_alicorp DROP COLUMN [cumplimiento];
  END;
  IF COL_LENGTH('dbo.encuestas_alicorp', 'atencion') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_alicorp_atencion SYSNAME;
   SELECT @constraint_encuestas_alicorp_atencion = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_alicorp') AND sc.name='atencion';
   IF @constraint_encuestas_alicorp_atencion IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_alicorp DROP CONSTRAINT [' + @constraint_encuestas_alicorp_atencion + ']');
   ALTER TABLE dbo.encuestas_alicorp DROP COLUMN [atencion];
  END;
  IF COL_LENGTH('dbo.encuestas_alicorp', 'proactividad') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_alicorp_proactividad SYSNAME;
   SELECT @constraint_encuestas_alicorp_proactividad = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_alicorp') AND sc.name='proactividad';
   IF @constraint_encuestas_alicorp_proactividad IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_alicorp DROP CONSTRAINT [' + @constraint_encuestas_alicorp_proactividad + ']');
   ALTER TABLE dbo.encuestas_alicorp DROP COLUMN [proactividad];
  END;
  IF COL_LENGTH('dbo.encuestas_alicorp', 'entregables_acordados') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_alicorp_entregables_acordados SYSNAME;
   SELECT @constraint_encuestas_alicorp_entregables_acordados = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_alicorp') AND sc.name='entregables_acordados';
   IF @constraint_encuestas_alicorp_entregables_acordados IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_alicorp DROP CONSTRAINT [' + @constraint_encuestas_alicorp_entregables_acordados + ']');
   ALTER TABLE dbo.encuestas_alicorp DROP COLUMN [entregables_acordados];
  END;
  IF COL_LENGTH('dbo.encuestas_alicorp', 'entregables_plazo') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_alicorp_entregables_plazo SYSNAME;
   SELECT @constraint_encuestas_alicorp_entregables_plazo = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_alicorp') AND sc.name='entregables_plazo';
   IF @constraint_encuestas_alicorp_entregables_plazo IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_alicorp DROP CONSTRAINT [' + @constraint_encuestas_alicorp_entregables_plazo + ']');
   ALTER TABLE dbo.encuestas_alicorp DROP COLUMN [entregables_plazo];
  END;
  IF COL_LENGTH('dbo.encuestas_alicorp', 'incidencias') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_alicorp_incidencias SYSNAME;
   SELECT @constraint_encuestas_alicorp_incidencias = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_alicorp') AND sc.name='incidencias';
   IF @constraint_encuestas_alicorp_incidencias IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_alicorp DROP CONSTRAINT [' + @constraint_encuestas_alicorp_incidencias + ']');
   ALTER TABLE dbo.encuestas_alicorp DROP COLUMN [incidencias];
  END;
  IF COL_LENGTH('dbo.encuestas_alicorp', 'incidencias_detectadas') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_alicorp_incidencias_detectadas SYSNAME;
   SELECT @constraint_encuestas_alicorp_incidencias_detectadas = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_alicorp') AND sc.name='incidencias_detectadas';
   IF @constraint_encuestas_alicorp_incidencias_detectadas IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_alicorp DROP CONSTRAINT [' + @constraint_encuestas_alicorp_incidencias_detectadas + ']');
   ALTER TABLE dbo.encuestas_alicorp DROP COLUMN [incidencias_detectadas];
  END;
  IF COL_LENGTH('dbo.encuestas_alicorp', 'solicitudes') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_alicorp_solicitudes SYSNAME;
   SELECT @constraint_encuestas_alicorp_solicitudes = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_alicorp') AND sc.name='solicitudes';
   IF @constraint_encuestas_alicorp_solicitudes IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_alicorp DROP CONSTRAINT [' + @constraint_encuestas_alicorp_solicitudes + ']');
   ALTER TABLE dbo.encuestas_alicorp DROP COLUMN [solicitudes];
  END;
  IF COL_LENGTH('dbo.encuestas_alicorp', 'solicitudes_atendidas') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_alicorp_solicitudes_atendidas SYSNAME;
   SELECT @constraint_encuestas_alicorp_solicitudes_atendidas = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_alicorp') AND sc.name='solicitudes_atendidas';
   IF @constraint_encuestas_alicorp_solicitudes_atendidas IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_alicorp DROP CONSTRAINT [' + @constraint_encuestas_alicorp_solicitudes_atendidas + ']');
   ALTER TABLE dbo.encuestas_alicorp DROP COLUMN [solicitudes_atendidas];
  END;
  IF COL_LENGTH('dbo.encuestas_alicorp', 'nps') IS NOT NULL
  BEGIN
   DECLARE @constraint_encuestas_alicorp_nps SYSNAME;
   SELECT @constraint_encuestas_alicorp_nps = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.encuestas_alicorp') AND sc.name='nps';
   IF @constraint_encuestas_alicorp_nps IS NOT NULL
     EXEC('ALTER TABLE dbo.encuestas_alicorp DROP CONSTRAINT [' + @constraint_encuestas_alicorp_nps + ']');
   ALTER TABLE dbo.encuestas_alicorp DROP COLUMN [nps];
  END;
 END;
 IF OBJECT_ID(N'dbo.coordinadores', N'U') IS NOT NULL
 BEGIN
  IF OBJECT_ID(N'dbo.respaldo_limpieza_coordinadores_20261012', N'U') IS NOT NULL
    THROW 51001, 'Ya existe el respaldo de coordinadores; revise antes de volver a ejecutar.', 1;
  SELECT * INTO dbo.respaldo_limpieza_coordinadores_20261012 FROM dbo.coordinadores;
  PRINT 'Respaldo generado para coordinadores';
  IF COL_LENGTH('dbo.coordinadores', 'password_hash') IS NOT NULL
  BEGIN
   DECLARE @constraint_coordinadores_password_hash SYSNAME;
   SELECT @constraint_coordinadores_password_hash = dc.name FROM sys.default_constraints dc
     INNER JOIN sys.columns sc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id=sc.column_id
     WHERE dc.parent_object_id=OBJECT_ID('dbo.coordinadores') AND sc.name='password_hash';
   IF @constraint_coordinadores_password_hash IS NOT NULL
     EXEC('ALTER TABLE dbo.coordinadores DROP CONSTRAINT [' + @constraint_coordinadores_password_hash + ']');
   ALTER TABLE dbo.coordinadores DROP COLUMN [password_hash];
  END;
 END;
 COMMIT;
 PRINT 'Migración completada. Copias de seguridad conservadas en dbo.respaldo_limpieza_*_20261012';
END TRY
BEGIN CATCH
 IF @@TRANCOUNT > 0 ROLLBACK;
 THROW;
END CATCH;
