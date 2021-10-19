# PSS pacs store service
a python microservice that consumes rabit queue and executes a storescu cli command
the microservice exports promateus monitoring information and includes health and readiness checks

### make sure the image can be pulled from a private repo
kubectl create secret docker-registry ghcred --docker-username=eyalto --docker-server=ghcr.io --docker-password=$CR_PAT

CT_PAR is a variable holding the Personal Access Tocken from github

### Installation 
helm install <name of service> psschart

values.yaml for the specific deployment can be overriden as follows in the helm install command:
<br/> --set pacs.host="host name/ip of listening pacs"
<br/> --set pacs.port="dicom tcp port of listening pacs"
<br/> --set rabbit.host="host ip/name of rabbitmq server"
<br/> --set rabbit.port="port of rabbitmq server"
<br/><br/>
The most important value is mapping the data volume
<br/>
  --set data.external_path= "<the paht on the host machine that will be mapped to internal path detault /zebra/data >"
  
### Customization and configuration

To change the configuration look at values.yaml 
Changes in the api/log/monitor/pacs/rabbit keys will be reflected in the configuration map
The configuration map places the config.json file according to the .Values.config.path direcory and sets the PSSCONFIG environment variable
  
In case you would like to use another configuration file it is possible by providing its path as value to PSSCONFIG environment variable
-- normally for local development just use config.json from the repository 
  
### FileSystem mount
  if you are using minikube make sure that the mount volume is accessible to the system e.g. 
``` minikube start --mount --mount-string="/data/folder/on/host:/zebe/data" ```
  in this case the data folder will just work with the values.yaml file
  
  
### Running 

  make sure the right hosts and ports are exposed to the running service
  api - portmap swagger webservice to make use of the web-api to send files to the pacs storage alternatively use curl

  #### Run examples
  1. create a rabbitmq docker container and run it locally
  ``` docker run -d -p 15672:15672 -p 5672:5672 rabbitmq:3-management ```
  2. create a pacs listener with dcmtk 
  ``` storescp -v -xcr "mv #f #f.dcm" -aet AEPACS 8080 ```
  3. start minikube
  ``` minikube start --mount --mount-string="/data/folder/on/host:/zebe/data" ```
  4. install helm chart and run
  ``` helm install mypss ./psschart ```
  5. port forward and send message though swagger 
  ``` kubectl port-forward <container name> 8001:8001 ```
  open the browser on swagger and send a message with dicom file path
  ``` http://localhost:8001/ ```
  or 
  ``` curl --request GET 'http://localhost:8001/pss?files=/zebra/data//pnx_positive/SERIES_214.2838012438.460.21423.44065.180880608466529/47b1d8c7.dcm'  ```
  
### Runtime customisation
  it is possible to add pacs addressing information inside the message to send a dicom to a diffenent pacs systems that are not configured (not tested)

