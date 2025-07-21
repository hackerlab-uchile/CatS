# Memoria CatS
## Sistema de caracterización de recursos web federado.

A federated web resource categorization system has been implemented, which
allows the creation of communities in charge of categorizing and classifying URLs through tags. Each tag can be associated with one of three possible actions: alert, notify or block a website. Communities have the ability to create as many tags as they wish, adapting the actions to the needs and values of their members.
On the other hand, users can subscribe or unsubscribe to the tags of the same or different community through a web extension.
Once subscribed to certain communities, users will see reflected in their browser the rules defined by these communities, applying the corresponding actions (alerts, notifications or blocking) according to the websites they visit.

The system is composed of three main components:
1. Telegram Bot, in charge of guiding step by step the creation of communities, managing the generation of tags, adding URLs to each tag and populating the database of the community.
2. Browser extension, in charge of direct interaction with the user, allowing the subscription to communities, the visualization of tags and the application of the actions declared by each community.
3. Database, in charge of storing all the information related to
communities, tags and URLs, together with their associated actions and justifications.

### Before run project 

Before running the project, make sure you have an .env file with the necessary credentials. You can use template.env as a guide.

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

*We are working on making the bot and extension publicly available for testing!!*