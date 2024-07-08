#!/bin/bash

docker run \
  -p8474:7474 -p8687:7687 \
  -v /store/projects/slango/neo4jdockerdata/data:/data \
  -v /store/projects/slango/neo4jdockerdata/logs:/logs \
  -v /store/projects/slango/neo4jdockerdata/import:/var/lib/neo4j/import \
  -v /store/projects/slango/neo4jdockerdata/plugins:/plugins \
  -v /store/projects/slango:/slango \
  -v ./neo4j/conf:/conf \
  --env NEO4J_AUTH=neo4j/password \
  --env NEO4J_PLUGINS='["bloom", "graph-data-science", "apoc", "apoc-extended"]' \
  graphstack/dozerdb:5.20.0.0-alpha.1
