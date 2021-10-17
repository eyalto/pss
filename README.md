# PSS pacs store service
a python microservice that consumes rabit queue and executes a storescu cli command

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
  
### Running 

  make sure the right hosts and ports are exposed to the running service
  api - portmap swagger webservice to make use of the web-api to send files to the pacs storage alternatively use curl

  
### Runtime customisation
  it is possible to add pacs addressing information inside the message to send a dicom to multiple or other pacs systems that are not configured by default

