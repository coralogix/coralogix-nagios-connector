# Coralogix Nagios Alerts Connector

# So how will it work ?
It is under few basic work assumptions we began working on this tool.
First, Coralogix's alerting functions are a great tool and we would like to make sure they are accessable to as many pepole as possiable.
Second, we recognize the fact that Nagios is a wide spread open source tool and is widely spead.
Third, connecting two opposite pieces usually requires some glue.
so let's get to Pasting :)

# The Technical Stuff
The tool is a web server designed to run on an EC2 instance and recieve alerts generated by coralogix as objects on S3.
and the nagios will query the same machine for either each alert or as a general query.

We choose to use instance rather then lambda since rapid queries may become quite expensive and a small ec2 instance ended up being the more frugal option.

We wanted to share the code for this solution so that anyone with a plan to use our solution along with nagios can have the freedom to do so.

# Prerequsites
All we actually need is an ec2 instance (with an Ubuntu image) along with an S3 bucket.
The instance will need an IAM role to allow read and write from that bucket.
We will also need a security group to be open to the ports we wish to serve.

# How to install?
1.Clone the repo:
```
git clone git@github.com:coralogix/coralogix-nagios-connector.git
```
2.run the setup script:
```
cd <repo folder>/scripts/
bash ./setup.sh --bucket <name of your s3 bucket>
```
at this point the service should be running and you can review the status of it by running:
```
#check the status
sudo systemctl status nagios-nest.service

#start the service
sudo systemctl start nagios-nest.service

#stop the service:
sudo systemctl stop nagios-nest.service
```
# How to use this connector?
Once the connector is up and running we need to point both coralogix and Nagios to it.
In coralogix you will need to configure a notification to send a webhook to the endpoint of your machine
the path of that endpoint is:
```
http://<your machine fqdn or IP>/alert-listener #Method POST
```

on the otherhand you will need to configure a nagios "test" to check for the status of each of the alerts.

Alternatively you can create a config automation in nagioswhich will query one of the endpoints of our new connector and manifest the nagios config portion from that.

# How to understand the connector's responses?
The connector will respond with an alert status as a json payload to the response to each request.
Additionaly we respond with different HTTP codes to help get a quicl bearing with minimal parsing on the nagios end of things.

HTTP 201 is alert triggered
HTTP 202 is alert resolved

When the coralogix hook is updating it's http endpoint it will respond with 200 if all goes well.

# A what are the options to query the adaptor?
```
#checking if the solutions is alive and listening incoming requests
/healthcheck

#will require the "alert_name" argument with the alert you wish to get a response to
/check-alert-status

# will generate the payload of the triggered alerts alone
/only_triggered_alerts 

# an endpoint to facilitate a forcefull resolution of an alert, will require "alert_name" argument
# HTTP method is POST
/resolve_alert 

```

# Does the solution provide any visual indication or a UI?
Yes.
While rudementry, we do provide a basic "read only" UI to allow better debugging and easy URL generation.