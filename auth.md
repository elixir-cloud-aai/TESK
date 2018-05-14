# Authentication and authorisation

TESK API integrates with [Elixir AAI](https://www.elixir-europe.org/services/compute/aai) via [OpenID Connect](http://openid.net/connect/) protocol to authenticate and authorise its users. In order to perform any TES operation (get and/or create tasks) TESK API user will have to have a valid account in Elixir AAI and belong to a specific Elixir group.

## Authentication
TESK API acts as a Resouce Server in the OIDC contract, whereas Elixir AAI plays the role of Authorisation Server. All of TESK API endpoints are secured, which means that in order to reach any of the endpoints, the request has to contain valid token issued by Elixir AAI, placed in `authorization: Bearer` header. 

### Obtaining a token
TESK API does not require, that the token is obtained using any specific client (application). Also token audience is not currently checked (not clear, if Elixir AAI supports defining token audience). Therefore, TESK API can be presented a token, that is:
* Not expired
* Obtained by user using any registered Elixir AAI client
* Obtained by user using any OIDC Flow
* Obtained by user using a client, that was granted `groupNames` scope (see [Authorisation](#authorisation))
* Containing any audience
* If Elixir AAI introduces groups-clients binding (presenting only those group names to clients, that where mentioned during client registration - currently each client receives all groups, as long as it has the scope `groupNames`), the token will have to be obtained using a client, which can receive those groups that are needed during Authorisation (see [below](#Authorisation))

#### Built-in client
A valid token can be obtained using an OIDC client built in Swagger UI at TESK API homepage. In order to use the client, it has to be configured, by placing Client ID - registered at Elixir AAI with Implicit Grant - in the API environment variable `TESK_API_SWAGGER_OAUTH_CLIENT_ID`. Unless groups-clients relationship is introduced, token obtained using Swagger UI from one environment can be used to make a call to API installed elsewhere.   

### Token validation
TESK API validates the token by hitting Elixir AAI `user_info` endpoint on each request and extracting information returned from that endpoint. If user info is returned without error, token is considered valid. Invalid token or lack of thereof in `authorisation: Bearer` header will result in `HTTP 401 Unauthorized` error. 

### Integrating with a different OIDC provider
We have not tested TESK API integration with a different OIDC provider than Elixir AAI, but since standard Spring OAuth library is used, it should be possible (just point [`security.oauth2.resource.user-info-uri`](#application.properties) to a proper URL), provided that the other Authorization Server provides information about the user in the same format that Elixir does. Otherwise changes to [GroupNamesSecurityExtractor](GroupNamesSecurityExtractor.java) and [ElixirPrincipalExtractor](ElixirPrincipalExtractor.java) will be necessary.

## Authorisation



