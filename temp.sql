USE tempdb;
GO

SELECT 
    o.name, 
    o.object_id, 
    l.request_session_id, 
    l.request_mode, 
    l.request_status
FROM sys.objects o
JOIN sys.dm_tran_locks l
    ON o.object_id = l.resource_associated_entity_id
WHERE o.name LIKE '#yourTempTableName%'
