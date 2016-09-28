LinkedDataInterface
====================

The Linked Data Interface represents the perfect way to share data from relational database
into a Semantic Web paradigm.

In this folder there is a complete system to obtain raw dara from database and convert it into a
N3Logic.

This data will be inferred thanks to a Rule engine Reasoner created with Jena libraries.

A Fuseki server installation will be the gate to extract this data using SPARQL or HTML endpoint.




Installation requirements
--------------------------

LinkedDataInterface need some requisites:

* Your own "mapping.ttl" file previously created with D2RQ.
* Your own "rules.txt" with several rules prepared to be inferred.
* Some knowledge of GNU/Linux.
* tomcat 8
* OpenJDK 8
* An Ubuntu 16.04 LTS operating system
