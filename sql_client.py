import logging
from contextlib import contextmanager
import pymysql

logger = logging.getLogger(__name__)

# SQL client wrapper for CRUD operations
class SqlClient:
    def __init__(self, host, name, user, password):
        # Save database connection parameters
        self.host=host
        self.db=name
        self.user=user
        self.password=password 
        logger.debug(f"MySQLClient initialized for DB: {name} on host: {host}")
    
    # Context manager for establishing and closing a MySQL connection
    @contextmanager
    def connection(self):
        logger.debug("Establishing MySQL database connection")
        try:
            # Try to connect to the database
            conn = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                db=self.db,
                cursorclass=pymysql.cursors.DictCursor
            )
            logger.debug("MySQL connection established successfully")
            yield conn
        except Exception as e:
            # Log and raise connection error
            logger.error(f"Failed to connect to MySQL database: {e}", exc_info=True)
            raise
        finally:
            logger.debug("Closing MySQL database connection")
            try:
                # Try to disconnect from the database
                conn.close()
                logger.debug("MySQL connection closed")
            except Exception as e:
                # Log disconnect error
                logger.error(f"Error closing MySQL connection: {e}", exc_info=True)
    
    # Helper function to execute SQL queries
    def _execute(self, sql, params=(), fetch=False):
        # Connect to database
        with self.connection() as conn:
            try:
                with conn.cursor() as cursor:
                    # Execute SQL query
                    cursor.execute(sql, params)
                    if fetch:
                        # Return all results for read
                        return cursor.fetchall()
                # Commit changes for create/update/delete
                conn.commit()
            except Exception as e:
                # Log and raise SQL query error
                logger.error(f"MySQL query failed: {e}", exc_info=True)
                raise
    
    # Create a new entry to a table
    def create_entry(self, entry, table):
        logger.debug(f"Adding entry into table: {table}")
        # Set up SQL query
        columns = ', '.join(entry.keys())
        placeholders = ', '.join(['%s']*len(entry))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        # Set up parameters
        params = tuple(entry.values())
        # Execute query
        self._execute(sql, params)
        logger.debug("Entry added successfully.")

    # Read all rows from a table
    def read_table(self, table):
        logger.debug(f"Reading all entries from table: {table}")
        # Set up SQL query
        sql = f"SELECT * FROM {table}"
        # Execute query
        results = self._execute(sql, fetch=True)
        logger.debug(f"Successfully read {len(results)} entries from table: {table}")
        # Return results
        return results or []

    # Update rows in a table that match filters
    def update_entry(self, updateValues, filters, table):
        logger.debug(f"Updating entry in table: {table}")
        # Set up SQL query
        setColumns = ", ".join(f"{col} = %s" for col in updateValues.keys())
        filterColumns = " AND ".join(f"{col} = %s" for col in filters.keys())
        sql = f"UPDATE {table} SET {setColumns} WHERE {filterColumns}"
        # Set up parameters
        params = tuple(updateValues.values()) + tuple(filters.values())
        # Execute query
        self._execute(sql, params)
        logger.debug(f"Entry updated successfully.")
    
    # Delete rows from a table that match filters
    def delete_entry(self, filters, table):
        logger.debug(f"Removing entry in table: {table}")
        # Set up SQL query
        filterColumns = " AND ".join(f"{col} = %s" for col in filters.keys())
        sql = f"DELETE FROM {table} WHERE {filterColumns}"
        # Set up parameters
        params = tuple(filters.values())
        # Execute query
        self._execute(sql, params)
        logger.debug(f"Entry removed successfully.")