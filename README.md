GitHubReplicator
================

# Description

GitHubReplicator is an application that replicates its own source in a new
GitHub repository when you navigate to its URL. 

When you navigate to its URL, it gets sufficient permissions to create a public
repository (which does not include access to private repositories). It then
forks the original repository at
<https://github.com/lkingsford/github_replicator.git> into a new fork in the
users GitHub profile. Finally, it redirects the browser to the new repository.

# Installation

## Required (assumed already set up):
- Debian 10 instance:

    - With root credentials
    - (Optionally) With DNS configured with A Record to that Debian instance

- GitHub Account in good standing

- Log into instance as root

## Register GitHub App

- Log on to GitHub using your account. 

- Navigate to <https://github.com/settings/applications/new>

- Set the Application Name as required. Set the homepage URL to the URL where
  the application is stored. Set the Authorization URL to 
  `[HOST]/github_callback` where `[HOST]` is the Hostname or IP address where
  the application is stored.

- Click 'Register Application'

- Store the 'Client ID' and the 'Client Secret' for use during the Server set up

## Server set up

- Install required packages

```
apt install nginx python3-pip python-dev certbot python-certbot-nginx git -y
pip3 install virtualenv
```

- Clone repository

> This is an active URL for the GitHubReplicator. Given the nature of the
> application, feel free to use a URL from a replicant repository.

```
git clone https://github.com/lkingsford/github_replicator.git
cd github_replicator
```

- Create and activate virtual environment

```
virtualenv -ppython3 env
. env/bin/activate
```

- Install required Python packages

```
pip install flask gunicorn python-dotenv requests
```

> The following steps are to set up the environment. Note that a .env file
> could be used (as shown here), or environment variables could be set
> appropriately for the platform (such as via the AWS Console or amending the
> Virtual Environment `activate` script

- Create the `.env` file by copying the `dotenv_template.txt` to `.env`

```
cp dotenv_template.txt .env
```

- Modify `.env` with your preferred text editor to set each value. A value is
  set by placing is directly after the appropriate `=` without a space,
  followed by a new line

    - `HOST` is the hostname of the server.
    - `GITHUB_CLIENT_ID` is the client ID shown by GitHub when creating the
       application.
    - `GITHUB_CLIENT_SECRET` is the client secret shown by GitHub when creating
       the application.
    - `STATE_KEY` is a cryptographically random string of numbers, and
       uppercase and lowercase letters, unique to the instance. It is
       recommended to generate it with KeePass or equivalent.
    - `LOG_FILENAME` is a location to store the log file. It is recommended to
       set it to a path inside the install folder - for instance,
       `/root/github_replicator/replicator.log`

- Use your preferred text editor to change the string SERVERNAME to the servername in `nginx_site_template.txt`

- Create the nginx site from the template

```
cp ngnix_site_template.txt /etc/nginx/sites-available/replicator
```

- Create the Gunicorn service

```
cp service_template /etc/systemd/system/replicator.service
service replicator start
```

  hostname of the server

- Make the site active

```
ln /etc/nginx/sites-available/replicator /etc/nginx/sites-enabled/replicator
```

- Create and install an SSL certificate

```
certbot --nginx
```
and follow the instructions ensuring you select to redirect all HTTP traffic to HTTPS

The site should now be active.