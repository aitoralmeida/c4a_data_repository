Alembic migration of the Rest Application Interface
====================================================

The current alembic migration is configured to use the alembic autogenerate procedure. To create a new version of the DB
it is necessary to perform the following steps:

1. Enter into the RestApiInterface folder ```cd /RestApiInterface```
2. Modify _alembic.ini_ and put database connection string, options........ 
3. Source virtualenv : ```source ./bin/activate```
4. run ```alembic revision --autogenerate -m "my migration procedure name"```
5. This will create a new file inside "versions" folder (See the current example in the folder).
6. Modify this file with the new database configurations. The __upgrade__ method will update the database and the
__downgrade__ method will revert the given modifications. Be sure to check that all is correct.
7. Run ```alembic upgrade head``` to upgrade to the current version.
8. Run ```alembic downgrade -1```To downgrade 1 version. It is possible to dongrade 1 or more versions (if available).


For more information about alembic, visit the following [link](http://alembic.zzzcomputing.com/en/latest/)