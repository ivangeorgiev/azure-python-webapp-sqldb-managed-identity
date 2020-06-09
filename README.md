# azure-python-webapp-sqldb-managed-identity

## Introduction

This is a sample application, used to test how Managed Identity authentication with Azure SQL Database can be implemented in Azure Web App. 

It should work as well in an Azure VM.

## Local Installation

To work on your local machine:

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Start the development server:

```bash
export FLASK_ENV="development"

flask run
```



## Prepare Managed Identity for Database Connectivity

This activity involves two steps:

* [Enable managed identity for App Service](https://docs.microsoft.com/en-us/azure/app-service/overview-managed-identity?tabs=python#using-the-azure-portal)

* [Enable managed identity for Azure SQL Database](https://docs.microsoft.com/en-us/azure/azure-sql/database/authentication-aad-configure?tabs=azure-powershell#create-contained-database-users-in-your-database-mapped-to-azure-ad-identities)

  You could achieve this using SSMS:

  ```sql
  CREATE USER <your app service name> FROM EXTERNAL PROVIDER;
  ALTER ROLE db_datareader ADD MEMBER <your app service name>
  ALTER ROLE db_datawriter ADD MEMBER <your app service name>
  ALTER ROLE db_ddladmin ADD MEMBER <your app service name>
  ```



## Azure Deployment Using Kudu Services

1. Create Azure Web App (i.e. `my-webapp`)
2. Open the Web App blade, section Deployment Center
3. Select and configure `Github` as a source
4. Use `Kudu` as deployment service



## Testing the Web App

Navigate to the root of your web app, e.g. https://my-webapp.azurewebsites.net to see the Azure SQL Database version:

```json
{
    "rows":[
        {"":"Microsoft SQL Azure (RTM) - 12.0.2000.8 \n\tMay 15 2020 00:47:08 \n\tCopyright (C) 2019 Microsoft Corporation\n"}
    ]
}
```

To get more exciting output, try the `/tables` endpoint which returns a list of tables in the database.

## Discussion

To authenticate:

1. Get Azure AD access token for accessing Azure SQL DB, using Azure Identity SDK for Python
2. Create connection string with a token.
3. Create pyodbc connection, using the connection string.

Above steps in a single `connect_db` function:

```python
def connect_db(server=None, database=None, driver=None):
    DB_SERVER = 'tcp:' + (server or os.environ['DB_SERVER']) + '.database.windows.net'
    DB_NAME = database or os.environ['DB_NAME']
    DB_DRIVER = driver or '{ODBC Driver 17 for SQL Server}'
    DB_RESOURCE_URI = 'https://database.windows.net/'

    az_credential = DefaultAzureCredential()
    access_token = az_credential.get_token(DB_RESOURCE_URI)
    
    token = bytes(access_token.token, 'utf-8')
    exptoken = b"";
    for i in token:
        exptoken += bytes({i});
        exptoken += bytes(1);
    tokenstruct = struct.pack("=i", len(exptoken)) + exptoken;
    
    connection_string = 'driver='+DB_DRIVER+';server='+DB_SERVER+';database='+DB_NAME
    conn = pyodbc.connect(connection_string, attrs_before = { 1256:bytearray(tokenstruct) });
    
    return conn
```

