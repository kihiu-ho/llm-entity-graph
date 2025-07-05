// Cypher script to remove Entity labels from Person and Company nodes
// Run these queries in Neo4j Browser to fix the label issue

// 1. Check current state - see what nodes have both specific and Entity labels
MATCH (n)
WHERE size(labels(n)) > 1 AND 'Entity' IN labels(n)
RETURN labels(n) as node_labels, count(n) as count
ORDER BY count DESC;

// 2. Check Person nodes with Entity label
MATCH (n:Person:Entity)
RETURN count(n) as person_nodes_with_entity_label;

// 3. Check Company nodes with Entity label
MATCH (n:Company:Entity)
RETURN count(n) as company_nodes_with_entity_label;

// 4. Remove Entity label from Person nodes
MATCH (n:Person:Entity)
REMOVE n:Entity
RETURN count(n) as person_nodes_fixed;

// 5. Remove Entity label from Company nodes
MATCH (n:Company:Entity)
REMOVE n:Entity
RETURN count(n) as company_nodes_fixed;

// 6. Verify the fix - check Person nodes
MATCH (p:Person)
RETURN labels(p) as person_labels, count(p) as count
ORDER BY count DESC;

// 7. Verify the fix - check Company nodes
MATCH (c:Company)
RETURN labels(c) as company_labels, count(c) as count
ORDER BY count DESC;

// 8. Check for any remaining Entity nodes (should be minimal or none)
MATCH (e:Entity)
WHERE NOT 'Person' IN labels(e) AND NOT 'Company' IN labels(e)
RETURN labels(e) as remaining_entity_labels, count(e) as count
ORDER BY count DESC;

// 9. Sample Person nodes (verify they only have Person label)
MATCH (p:Person)
RETURN p.name, labels(p) as labels
LIMIT 10;

// 10. Sample Company nodes (verify they only have Company label)
MATCH (c:Company)
RETURN c.name, labels(c) as labels
LIMIT 10;

// 11. Check relationships between Person and Company nodes
MATCH (p:Person)-[r]->(c:Company)
RETURN type(r) as relationship_type, count(r) as count
ORDER BY count DESC
LIMIT 10;

// 12. Final verification - ensure no Person or Company nodes have Entity label
MATCH (n)
WHERE ('Person' IN labels(n) OR 'Company' IN labels(n)) AND 'Entity' IN labels(n)
RETURN labels(n) as problematic_labels, count(n) as count;

// Expected result for query 12: No rows returned (count should be 0)
// This confirms that Person and Company nodes have only specific labels
