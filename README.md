# Slango


## Starting
- Execute the script `start_dozer` to start a [DozerDB](http://dozerdb.org/) instance configured according to `neo4j/config` files.
- Open http://localhost:8474 to access the web interface
- The bolt interface is reachable under `bolt://localhost:8687`

```bash
pv milz21.cypher | sed "s/CREATE CONSTRAINT ON/CREATE CONSTRAINT FOR/g"| sed "s/\(CREATE CONSTRAINT .*\) ASSERT/\1 REQUIRE/g" | cypher-shell -a localhost:8687 -u neo4j -p password -d milz26
```