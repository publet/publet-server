# Marketo integration

This document describes what information Publet needs in order to make requests
to the Marketo API.

## Endpoint URL

Publet needs to know the endpoint URL of your Marketo instance.  You can find it
within the Marketo Admin -> Web Services panel.

[More here](http://developers.marketo.com/documentation/rest/endpoint-url/)

## Custom service

In order for Publet to use the REST API of your Marketo instance, you have to
create a Custom Service.  This service will allow you to control what levels of
access Publet will be afforded.  Once the service is created, please let us know
what client ID and client secret we should use when making API requests.

[More here](http://developers.marketo.com/documentation/rest/authentication/)

## Where to find data from Publet

Once Publet has all the necessary pieces of configuration, it will start to send
data to your Marketo instance.  This is done automatically as new data is
collected by Publet.  At this time, there is no batching of requests so
everything should come as it happens.

When a lead form is filled out and submitted on the Publet platform, we will
store the information in our database, and then use the API to create new leads
in your Marketo instance.  Form submissions will appear as new leads in Marketo.

