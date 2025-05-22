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

Also, remember to have Docker installed and running!!

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
3. Search for _CatS\_extension\_bot_ and add it
4. Start communication with /start

(Remember that to interact with the bot the project must be running first)


### Stop and restart the project

In case that you need to shut down de project and restart, run the follow commands to ensure that the docker cache do not affect in the execute:

```
docker-compose down --remove-orphans
docker image prune -a
docker-compose up --build
```