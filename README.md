# Homestack
[Homestack](https://github.com/geudrik/homestack) is my attempt at a unified and centralized home automation / home lab management front end and API.

Homestack has two primary parts - a WebUI and an API. The WebUI leverages [Gentelella](https://github.com/puikinsh/gentelella) (because it's super sexy)

I'll write up additional details as this side project moves forward.


### Config File
This whole project depends on a shared configuration file, conviently located in `~/.config/homestack`, or loaded from the `HOMESTACK_CONFIG` environment variable. The config file should looke the following

```sql
[homestack]
secret=some long complicated and secret string

[homestack_databases]
user=root
pass=
host=localhost
port=3306
name=homestack
keep_alive=true

[redis]
host=localhost
port=

[logging]
# Logging level for Homestack. DEBUG,INFO,WARNING,ERROR,CRITICAL
level=DEBUG

[argon2]
# The number of rounds to perform
rounds=2500

# How much  memory to use? This is set to 1M by default. Higher values will greatly increase the time it takes, esp when you up memory with rounds together. These settings take about 1S on a v3 i7
memory=1024
```

### Dependencies
* Homestack DB Library: `pip install git+git://github.com/geudrik/homestack-db-library.git`
* Redis: `sudo apt-get install redis`

### Python Requirements
```
flask
flask-principal
flask-login
redis
sqlalchemy
passlib
```
