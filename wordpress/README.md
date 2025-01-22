# Wordpress Tools

## Development with Wordpress API
### (optional) Run Wordpress locally with docker:
create a yaml file `wordpress.yaml`:

```yaml
services:

  wordpress:
    image: wordpress
    restart: always
    ports:
      - 8070:80
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_USER: dbuser
      WORDPRESS_DB_PASSWORD: dbpassword
      WORDPRESS_DB_NAME: exampledb
    volumes:
      - wordpress:/var/www/html

  db:
    image: mysql:8.0
    restart: always
    environment:
      MYSQL_DATABASE: exampledb
      MYSQL_USER: dbuser
      MYSQL_PASSWORD: dbpassword
      MYSQL_RANDOM_ROOT_PASSWORD: '1'
    volumes:
      - db:/var/lib/mysql

volumes:
  wordpress:
  db:

```
and run `docker compose -f wordpress.yaml up`.

### CRITICAL: Configure Permalinks in Settings
Without configuring permalinks, the Wordpress API will not work, because the `/wp-json` endpoint will not be available.
To do this, go to your wordpress site dashboard, on the left sidebar, select `Settings` -> `Permalinks`, then select any non-plain Permalink structure.

