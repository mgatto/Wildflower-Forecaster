Generate Base Schema
====================

env.py already imports models.entities and sets a path.

su - www-data
(else you will get a permission denied error when it tries to
write the version script to /versions; sudo does not help since we're in a
virtualenv, in which case when in sudo, the entire virtualenv and all its
scripts are unavailable)

cd /srv/www/api.local/trellis_api/models
(you should be in the same directory as alembic.ini)

source ../../../../env/bin/activate

alembic revision --autogenerate -m "Base Schema"
alembic upgrade --sql HEAD

(--sql is good for testing without actually committing)



From the Docs
=============

"Autogenerate can not detect:

    Changes of table name. These will come out as an add/drop of two different tables, and should be hand-edited into a name change instead.
    Changes of column name. Like table name changes, these are detected as a column add/drop pair, which is not at all the same as a name change.
    Special SQLAlchemy types such as Enum when generated on a backend which doesn't support ENUM directly - this because the representation of such a type in the non-supporting database, i.e. a CHAR+ CHECK constraint, could be any kind of CHAR+CHECK. For SQLAlchemy to determine that this is actually an ENUM would only be a guess, something that’s generally a bad idea. To implement your own “guessing” function here, use the sqlalchemy.events.DDLEvents.column_reflect() event to alter the SQLAlchemy type passed for certain columns and possibly sqlalchemy.events.DDLEvents.after_parent_attach() to intercept unwanted CHECK constraints."

"Autogenerate can't currently, but will eventually detect:

    Free-standing constraint additions, removals, like CHECK, UNIQUE, FOREIGN KEY - these aren’t yet implemented. Right now you’ll get constraints within new tables, PK and FK constraints for the “downgrade” to a previously existing table, and the CHECK constraints generated with a SQLAlchemy “schema” types Boolean, Enum.
    Index additions, removals - not yet implemented.
    Sequence additions, removals - not yet implemented."
