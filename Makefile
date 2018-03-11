ECR_REPO=698514710897.dkr.ecr.us-west-1.amazonaws.com
APP_NAME=mappening/backend

##########################      AWS / PRODUCTION      ##########################

# Authenticate Docker client
ecr-login:
	$(shell aws ecr get-login --no-include-email --region us-west-1)

# Build backend image
build:
	docker build ./src -t $(APP_NAME)

# Login, build, and push latest image to AWS
push: ecr-login build
	docker tag $(APP_NAME):latest $(ECR_REPO)/$(APP_NAME):latest
	docker push $(ECR_REPO)/$(APP_NAME):latest

##################       LOCAL DEVELOPMENT (Backend Only)     ################## 

# Build and run backend image
dev: build
	docker run --rm --name backend-dev -v $(shell pwd)/src:/app -p "5000:5000" -it $(APP_NAME)

# Stop running containers
stop:
	-docker ps | tail -n +2 | cut -d ' ' -f 1 | xargs docker kill


#######################       SPHINX DOCUMENTATION     ######################### 

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = Mappening
SOURCEDIR     = .
BUILDDIR      = _build

# Need pip to be installed
setup:
	pip install -r ./src/requirements.txt

sudo-setup:
	sudo pip install -r ./src/requirements.txt

# Help for sphinx usage
sphinx-help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  e.g. `make html`
# $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
