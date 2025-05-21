# Memoria CatS

### Before run project 

Before running the project, make sure you have an .env file with the necessary credentials (Server ip, database url and bot token). You can follow the next example:

```
PYTHONPATH="backend_path"

# ---- Server ----
SERVER_IP = "ip"

# ---- Database ----
DATABASE_URL= "db_url"

# ---- Backend ----
BOTTOKEN = "token"
```

### Run project
1. Go to the "backend" folder
2. Build containers: 

    ```
    docker-compose build
    ```
3. Run services:

    ```
    docker-compose up
    ```

### CatS bot

To interact with the bot:
1. Create a telegram group
2. Go to add member
3. Search for CatS bot and add
4. Start communication with /start

(Remember that to interact with the bot the project must be running first)