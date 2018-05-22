# Authentication and authorisation

TESK API integrates with [Elixir AAI](https://www.elixir-europe.org/services/compute/aai) via [OpenID Connect](http://openid.net/connect/) protocol to authenticate and authorise requests. Authentication and authorisation are optional and can be switched off completely. When authentication is on, in order to perform any TES operation (get and/or create tasks) TESK API user will have to include a valid access token issued by Elixir AAI in the request header. To obtain such a token, a user will have to:
* have a valid account in Elixir AAI
* belong to a specific Elixir group
* have access to a registered Elixir client application, that was assigned - among others - `groupNames` scope.

## Switching on/off authentication and authorisation
Authentication and authorisation can be globally switched on and off for TESK API using [Spring Profiles](https://docs.spring.io/spring-boot/docs/current/reference/html/boot-features-profiles.html). When the default `noauth` profile is active, all endpoints are unauthenticated and all (also previously) created TES tasks are visible to any user. New tasks are labelled as created by `anonymousUser` and no team ownership is assigned to new tasks. With `auth` profile activated, all the rules described below apply. The way to activate each of the profiles is described [here](README.md#externalized-configuration).

## Authentication
The TESK API acts as a Resource Server in the OIDC contract, whereas Elixir AAI plays the role of Authorization Server. All of TESK API endpoints are secured, which means that in order to reach any of the endpoints, the request has to contain a valid _access_token_ issued by Elixir AAI, placed in `authorization: Bearer` header. 

### Obtaining a token
At the moment (subject to change) TESK API does not require the access token to be obtained using any specific client (application). Also the token audience is not currently checked (it is not clear, if Elixir AAI supports defining a token audience). Therefore, a valid token has the following properties:
* Access token
* Not expired
* Obtained by a user using any registered Elixir AAI client
* Obtained by a user using any OIDC Flow
* Obtained by a user using a client, that was granted `groupNames` scope (see [Authorisation](#authorisation))
* Containing any audience
* If Elixir AAI introduces groups-clients binding (presenting only those group names to clients, that where mentioned during client registration - currently each client receives all groups, as long as it has the scope `groupNames`), the token will have to be obtained using a client, which can receive those groups that are needed during Authorisation (see [below](#Authorisation))

#### Built-in client
A valid token can be obtained using an OIDC client built in Swagger UI at the TESK API homepage. In order to use the client, it has to be configured, by placing Client ID - registered at Elixir AAI with Implicit Grant - in the API environment variable `TESK_API_SWAGGER_OAUTH_CLIENT_ID` (authorisation code grant also possible, but discouraged). Unless groups-clients relationship is introduced, token obtained using Swagger UI from one environment can be used to make calls to API installed elsewhere.   

### Token validation
TESK API validates the token by hitting Elixir AAI `user_info` endpoint on each request and extracting information returned from that endpoint. If user info is returned without error, token is considered valid. Invalid token or lack of thereof in `authorisation: Bearer` header will result in `HTTP 401 Unauthorized` error. 

### Integrating with a different OIDC provider
We have not tested TESK API integration with a different OIDC provider than Elixir AAI, but since standard Spring OAuth library is used, it should be possible (just point [`security.oauth2.resource.user-info-uri`](#application.properties) to a proper URL), provided that the other Authorization Server provides information about the user in the same format that Elixir does. Otherwise changes to [GroupNamesSecurityExtractor](src/main/java/uk/ac/ebi/tsc/tesk/config/security/GroupNamesSecurityExtractor.java) and [ElixirPrincipalExtractor](src/main/java/uk/ac/ebi/tsc/tesk/config/security/ElixirPrincipalExtractor.java) will be necessary.

## Authorisation
TESK API uses Elixir AAI group membership to authorise users. Elixir recognises group managers and members, but only includes information about the latter in `user_info` endpoint response. Therefore a nested structure of groups is used by us to reflect different roles of users.
### Group structure
Group level | Example (from our own environments) | Meaning | Multiplicity
------------ |---| -------------|---
Base Group | GA4GH:GA4GH-CAP | Base group, representing all TESK environments. All other groups are subgroups of this groups. Does not have meaning on its own. | There can be only one per TESK installation.
Environment Group| GA4GH:GA4GH-CAP:EBI | Direct subgroup of base group, representing TESK environment/installation (EBI or CSC for environments managed by us) | There can be only one per TESK installation.
Super Admin Group | GA4GH:GA4GH-CAP:EBI:ADMIN | Direct subgroup - named ADMIN - of environment group, representing admins of the whole TESK installation (in our case Admins of TESK installed in EBI) | There can be only one per TESK installation.
Team Group | GA4GH:GA4GH-CAP:EBI:SDO | Direct subgroup - named anything else than ADMIN - of environment group. Represents a group of co-workers. | There can be many for each TESK installation with any names other than ADMIN.
Team Admin Group | GA4GH:GA4GH-CAP:EBI:SDO:ADMIN | Direct subgroup - named ADMIN - of team group. Represents a group of users, being admins of a team group.| One per team group; many per TESK installation.

### Endpoint permissions

Endpoint | Objective | Condition 
------------ |---|--
Create a task | A task must be created by a specific user and for up to one specific team (no team or one team). | User must be a member of _any_ Team Group or a Super Admin to create a task. If a user is a member of more than one Team Group, a user can specify, for which team to create a task (by putting team name in `tags['GROUP_NAME']`. If no team is specified, task will still be created for a randomly chosen team. If a user does not belong to any team (is a Super Admin only), task is still created, but does not belong to any team (only other Super Admins will be able to see it).
Get a task | A team member can only see tasks, that were created by him/her. A team admin can see all tasks created for his/her team. A super admin can see all tasks. | User must be a member of _the_ Team Group, that the task was created for AND be _the_ task creator OR user must be an admin of _the_ Team Group, that _the_ task was created for OR user must be a Super Admin.
Cancel a task | User can cancel those tasks that are visible to him/her (as for `Get a task`). | User must be a member of _the_ Team Group, that _the_ task was created for AND be _the_ task creator OR user must be an admin of _the_ Team Group, that _the_ task was created for OR user must be a Super Admin.
List tasks | User can list those task that are visible to him (as for `Get a task`). | User must be a member of _any_ Team Group OR user must be an admin of _any_ Team Group OR user must be a super admin to access `List tasks` enpoint. The response contains those tasks, that are visible to the user (rules from `Get a task` apply).

### Examples
* User '123' with group `GA4GH:G4GH-CAP:EBI:SDO` creates a task at TESK installed in `EBI`. Task created by user 123, for team SDO.
* User '123' with groups `GA4GH:G4GH-CAP:EBI:SDO`, `GA4GH:G4GH-CAP:EBI:TEST` creates in `EBI` a task without tags. Task created by user 123, for - randomly chosen - team SDO.
* User '123' with groups `GA4GH:G4GH-CAP:EBI:SDO`, `GA4GH:G4GH-CAP:EBI:TEST` creates a task with tags: ```{"tags" : {"GROUP_NAME" : "TEST"}}``` Task created by user 123, for team TEST.
* User '123' with group `GA4GH:G4GH-CAP:EBI` creates a task at TESK installed in `EBI`. Forbidden, no task created --> no team membership
* User '123' with group `GA4GH:G4GH-CAP:EBI:ADMIN` creates a task at TESK installed in `EBI`. Task created by user 123, without group assignment.
* User '123' with group `GA4GH:G4GH-CAP:EBI:SDO:ADMIN` creates a task at TESK installed in `EBI`. Elixir additionally treats such a user as a member of all parent groups, so the user also belongs to a group `GA4GH:G4GH-CAP:EBI:SDO` - so task will be created for group SDO (otherwise - if not Elixir special handling of nested membership and only taken TESK API rules into account - would be Forbidden).
* User '123' with group `GA4GH:G4GH-CAP:CSC:SDO` creates a task at TESK installed in `EBI`. Forbidden - no permissions to create tasks in `EBI`.
* User '123' with group `GA4GH:G4GH-CAP:EBI:SDO` gets a task created by user 123, for team SDO via TESK installed in `EBI`. Success.
* User '124' with group `GA4GH:G4GH-CAP:EBI:SDO` gets a task created by user 123, for team SDO via TESK installed in `EBI`. Forbidden (not his/her task).
* User '123' with group `GA4GH:G4GH-CAP:EBI` only, gets a task created by user 123, for team SDO via TESK installed in `EBI`. Forbidden (not SDO group member anymore).
* User '123' with group `GA4GH:G4GH-CAP:EBI:SDO:ADMIN`, gets a task created by user 123, for team SDO via TESK installed in `EBI`. Success.
* User '124' with group `GA4GH:G4GH-CAP:EBI:SDO:ADMIN`, gets a task created by user 123, for team SDO via TESK installed in `EBI`. Success (team group admin sees all team tasks).
* User '124' with group `GA4GH:G4GH-CAP:EBI:ADMIN`, gets a task created by user 123, for team SDO via TESK installed in `EBI`. Success (super admin sees everything). 
* User '123' with group `GA4GH:G4GH-CAP:EBI:SDO` gets a task list. Success. List contains all tasks created for SDO by user 123.
* User '123' with group `GA4GH:G4GH-CAP:EBI` only, gets a task list. Forbidden (not a team member, neither team admin, nor super admin).
* User '123' with group `GA4GH:G4GH-CAP:EBI:SDO:ADMIN`, gets a task list. Success. List contains all tasks created for team SDO by all users.
* User '124' with group `GA4GH:G4GH-CAP:EBI:ADMIN`, gets a task list. Success. List contains all tasks created for all/no teams by all users.
* User '123' with groups `GA4GH:G4GH-CAP:EBI:TEST` and `GA4GH:G4GH-CAP:EBI:SDO:ADMIN`, gets a task list. Success. List contains all tasks created for team TEST by user 123 and also all tasks created for team SDO by all users.

### Configuration
Parts of Elixir groups 'authorisation framework' - particularly base group name, environment subgroup name and ADMIN subgroup name - are configurable in [the same way](README.md#externalized-configuration) that is used throughout TESK API.

Environment variable | Meaning | Default
------------ |---|--
`TESK_API_AUTHORISATION_PARENT_GROUP` | Full name of the base group (with default `elixir:` prefix, which is added by Elixir to all group names) | `elixir:GA4GH:GA4GH-CAP`
`TESK_API_AUTHORISATION_ENV_SUBGROUP` | Name of the subgroup representing environment (aka Environment Group) | `EBI` (Full group name:  `elixir:GA4GH:GA4GH-CAP:EBI`)
`TESK_API_AUTHORISATION_ADMIN_SUBGROUP` | Name of the subgroup representing admins (super admins or team admins) | `ADMIN` (Full group name of super-admins:  `elixir:GA4GH:GA4GH-CAP:EBI:ADMIN`)

