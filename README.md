# BMaps-Backend 

## Documentation
Hosted on GitHub Pages at http://ucladevx.com/BMaps-Backend/

## Setting Up the Environment
- Follow instructions in main [BMaps](https://github.com/ucladevx/BMaps) repository
- Install git-crypt
- Generate an RSA gpg key at least 2048 bits in length. Email the key to a bmaps member familiar with the operation of git-crypt. Pull down the changes from the master branch after the bmaps member has told you to do so.
- Run `git-crypt unlock`
- Build the base image that contains all dependencies that are fairly static but take a while to install
  - `make build-base`
- NOTE: the database connection doesn't seem to work over UCLA_WEB wifis, a more secure connection is needed (UCLA_WIFI)

## How to Run Backend Locally

- Build and run container using local Postgres database
  - `make dev`
  - To use production database (not recommended for local development):
    - `make prod`
- Navigate to [http://localhost](http://localhost)
- Access flask api directly at port [5000](http://localhost:5000/)
  - Use `localhost:5000/api/<insert_api_route_here>`
  - e.g. `localhost:5000/api/events`
- Stop running with `CTRL+C` or `make stop` in a separate terminal window

## Repo Breakdown

- Database config/data is in `/database`
- Backend source code is in `src/`
- tkinter GUIs is in `tkinter/`
- Autodocumentation is in `docs/`
- Beautiful Soup Scraping is in `scraping/` 

## Using git crypt to get access to .env files

- Generate a rsa2048 gpg key using the gpg tool
  - `gpg full-generate-key`
  - Make sure to record your passphrase in a secure location, and also to generate a revocation certificate for the key in case it gets compromised or lost
    - `gpg --output revocation-cert.asc --gen-revoke <PUB-KEY-SIG>`
- Convey your gpg key through a keyfile securely to a project member, either using a pub key server, or through another clandestine channel
  - To generate the key file:
    - `gpg --output <YOUR_NAME>.gpg --export <PUB-KEY-SIG>`
- The team member will then add your pub-key to their gpg key-chain using 
  - `gpg --import <keyfile>`
  - Note that keyfile in this step is the same as the <YOUR_NAME>.gpg file generated in the previous step
  - They may also choose to sign the key if they trust you.
- Finally, the team member will run:
  - `git-crypt --add-gpg-user <team member to be added's email or any other identifier of key>`
  - Then they must push their changes (adding your pub key) made to the repository to the remote, and those changes pulled by you
  - Note that their changes will not appear when `git status` is run, so it may be necessary to make some other change in the repository to successfully push the newly added pub key within git crypt
- Finally, once you have the updated repository they pushed, run
  - `git-crypt unlock`
  - you will not need to run git-crypt unlock again, since git-crypt will automatically encrypt your .envs as you push them within this repo, and decrypt them as they are pulled from the remote. GLHF.

