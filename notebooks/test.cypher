MATCH (p:Code)-[:PARENT_OF]->(c:Code) 
WHERE p.code = 'E11'
RETURN c