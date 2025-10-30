"""
db_config.py
-----------
Description:
   Database configuration settings for the Geometric Learning System.
   Contains connection parameters for SQL Server instances.
   Configured for local development with multiple developer setups.

Author: Karin Hershko and Afik Dadon
Date: February 2025
"""



# Nicole
DB_CONFIG = {
    'driver': 'SQL Server',
    'server': 'DESKTOP-824DEOL\SQLEXPRESS01',
    'database': 'AKINTOR',
    'trusted_connection': 'yes'
}



# Karin
# DB_CONFIG = {
#    'driver': 'SQL Server',
#    'server': 'OG-PROLECTS\SQLEXPRESS',
#    'database': 'FinalProject',
#    'trusted_connection': 'yes'
# }
