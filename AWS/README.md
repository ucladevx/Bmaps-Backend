# AWS

Contains all the files for deployment. Should be maintained alongside files in AWS instance (reached through `make ssh`). Instructions for dealing with AWS are as follows.

## To Deploy
* `cd` to the Mappening-Backend repository
* Build + Push a new image to AWS with `make push`
  * Just build with `make build`
* In separate tab/window run `make ssh` to login to AWS instance
* Deploy with `make deploy`
* Navigate to `52.53.72.98`
  * Access static files with nginx with `/` or `/imgs`
    * e.g. `52.53.72.98/imgs`
  * Access flask api by forwarding requests through nginx
    * Use `/api/v1/insert_api_route_here`
    * e.g. `52.53.72.98/api/v1/events`
  * Can also access flask server directly at port 5000
    * e.g. `52.53.72.98:5000/api/events`
* Stop running on ubuntu with `CTRL+C`

## To Add New Container
* Log in to AWS account [here](devx-dora.signin.aws.amazon.com/console)
* Click on Services > Compute > Elastic Container Service > Repositories 
* Click `Create repository` and give it a name `<repo_name>`
* Click `Next step` and ignore the instructions supplied
* In Mappening-Backend, modify the Makefile
  * Add new app name var: `APP_NAME_<repo_name>=<repo_name>`
  * Add new line to `build` target: `docker build ./<repo_name> -t $(APP_NAME_<repo_name>)`
  * Add new lines to `push` target: 
    * `docker tag $(APP_NAME_<repo_name>):latest $(ECR_REPO)/$(APP_NAME_<repo_name>):latest`
    * `docker push $(ECR_REPO)/$(APP_NAME_<repo_name>):latest`
* If new container runs on a new port, follow the instructions below to edit the instance
* Otherwise, deploy as normal to AWS and all should work (hopefully)


## To Edit Instance/Open New Port
* Log in to AWS account [here](devx-dora.signin.aws.amazon.com/console)
* Click on Services > Compute > EC2 > Repositories > Instances
* Click on your running instance 
* On the bottom of the screen, you can modify instance Tags or create Alarms
* On the far right of the screen, under the Security Groups filter, click the link
* On the bottom of the screen, click Inbound > Edit 
* New ports can now be opened by clicking `Add Rule` and adding a Custom TCP Rule using the approrpiate Port Range
