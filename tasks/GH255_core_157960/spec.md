# GH255_core_157960: Add support for health_overview API endpoint to Tractive integration — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/151651
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

Hello, 
Everything used to work perfectly, but since a few days, all the Tractive sensors report Unavailable .
All the Diagnostic part work great though.

<img width="687" height="1077" alt="Image" src="https://github.com/user-attachments/assets/c240afac-8e20-4046-8175-5140ee53757c" />

<img width="789" height="786" alt="Image" src="https://github.com/user-attachments/assets/9a74f8aa-2b89-4543-9363-7d0b17ad7d7b" />

I tried deleting and reinstalling the Device but the problem remains.
Thanks for your help!

### What version of Home Assistant Core has the issue?

## System Information  version | core-2025.8.3 -- | -- installation_type | Home Assistant OS dev | false hassio | true docker | true container_arch | amd64 user | root virtualenv | false python_version | 3.13.3 os_name | Linux os_version | 6.12.41-haos arch | x86_64 timezone | America/Toronto config_dir | /config  <details><summary>Home Assistant Community Store</summary>  GitHub API | ok -- | -- GitHub Content | ok GitHub Web | ok HACS Data | ok GitHub API Calls Remaining | 5000 Installed Version | 2.0.5 Stage | running Available Repositories | 2172 Downloaded Repositories | 33  </details>  <details><summary>AccuWeather</summary>  can_reach_server | ok -- | -- remaining_requests | 45  </details>  <details><summary>Home Assistant Cloud</summary>  logged_in | false -- | -- can_reach_cert_server | ok can_reach_cloud_auth | ok can_reach_cloud | ok  </details>  <details><summary>Home Assistant Supervisor</summary>  host_os | Home Assistant OS 16.1 -- | -- update_channel | stable supervisor_version | supervisor-2025.08.3 agent_version | 1.7.2 docker_version | 28.3.3 disk_total | 234.0 GB disk_used | 52.7 GB healthy | true supported | true host_connectivity | true supervisor_connectivity | true ntp_synchronized | true virtualization |  board | generic-x86-64 supervisor_api | ok version_api | ok installed_addons | AdGuard Home (5.3.2), Plex NAS (1.42.1.10060-4e8b05daf-ls278), Prowlarr NAS (2.0.5.5160-ls125), Sonarr (4.0.15.2941-2), qBittorrent (5.1.2-7), Radarr (5.26.2.10099), Get HACS (1.3.1), Studio Code Server (5.19.3), Tailscale (0.25.0), Hydroqc Add-on (v2.0.0-1), Mosquitto broker (6.5.1), Overseerr (1.34.0), changedetection (0.50.11), Advanced SSH & Web Terminal (21.0.2), Home Assistant Google Drive Backup (0.112.1), Music Assistant Server (2.5.8), Cloudcommander (18.7.3), Spotify Connect (0.15.0), Notifiarr (0.8.3), Samba share (12.5.2), FTP (5.3.2), Nextcloud (31.0.8), Portainer (2.33.0), Sabnzbd (4.5.3), SABnzbd (0.5.0), Newt Add-on (1.4.2), Cloudflared (5.3.8), OpenSpeedTest (v2.0.6), ngrok Client Installer (Unofficial) (15.0.5.3.0), Lidarr NAS (2.13.3.4711), eufy-security-ws (1.9.3), Frigate (0.16.0), HassOS SSH port 22222 Configurator (0.9.3), Glances (0.21.1), Rclone Backup (3.3.4), Tautulli (4.2.1), Filebrowser (2.42.5), Home-Assistant-Matter-Hub (3.0.0-alpha.87)  </details>  <details><summary>Dashboards</summary>  dashboards | 4 -- | -- resources | 21 views | 2 mode | storage  </details>  <details><summary>Network Configuration</summary>  adapters | lo (disabled), enp2s0 (enabled, default, auto), docker0 (disabled), hassio (disabled), veth87cc3ac (disabled), vethcad6720 (disabled), vetha5077c0 (disabled), veth6573f0e (disabled), veth0a60a72 (disabled), vethd95be71 (disabled), veth4c90ff6 (disabled), veth20a4004 (disabled), vethe5288d1 (disabled), vethe4bee7a (disabled), veth2c5d6b6 (disabled), veth1bba40e (disabled), veth8caec6f (disabled), vethcaef93f (disabled), vethd04cc7d (disabled), vethc059d7c (disabled), vethb8d27ee (disabled), vethc9cd1f2 (disabled), vethde1ac5b (disabled), veth09aa42f (disabled), vetheebba0a (disabled) -- | -- ipv4_addresses | lo (127.0.0.1/8), enp2s0 (192.168.2.10/24), docker0 (172.30.232.1/23), hassio (172.30.32.1/23), veth87cc3ac (), vethcad6720 (), vetha5077c0 (), veth6573f0e (), veth0a60a72 (), vethd95be71 (), veth4c90ff6 (), veth20a4004 (), vethe5288d1 (), vethe4bee7a (), veth2c5d6b6 (), veth1bba40e (), veth8caec6f (), vethcaef93f (), vethd04cc7d (), vethc059d7c (), vethb8d27ee (), vethc9cd1f2 (), vethde1ac5b (), veth09aa42f (), vetheebba0a () ipv6_addresses | lo (::1/128), enp2s0 (fd1b:c992:9b6a:208b:7f87:b6d5:93a1:6490/64, fe80::cf6d:e585:b8f8:8919/64), docker0 (fe80::e0bc:9aff:fe4e:e27/64), hassio (fe80::3046:a9ff:febd:ff75/64), veth87cc3ac (fe80::3419:c3ff:febc:9c/64), vethcad6720 (fe80::f87b:abff:fed3:e972/64), vetha5077c0 (fe80::7c31:9bff:fee6:1d9f/64), veth6573f0e (fe80::4bc:f5ff:fe49:d221/64), veth0a60a72 (fe80::20b3:9fff:fe02:4ef8/64), vethd95be71 (fe80::9837:edff:fe5e:4493/64), veth4c90ff6 (fe80::5c5e:bcff:fe38:6bd7/64), veth20a4004 (fe80::4f:1dff:fecb:6e7d/64), vethe5288d1 (fe80::5053:32ff:feb4:c72a/64), vethe4bee7a (fe80::5887:7ff:fe41:d963/64), veth2c5d6b6 (fe80::684a:c3ff:fe72:1af2/64), veth1bba40e (fe80::45a:31ff:fed7:ca4e/64), veth8caec6f (fe80::ecda:88ff:fee0:5ec1/64), vethcaef93f (fe80::6c82:bdff:fec4:dd6/64), vethd04cc7d (fe80::dc92:3eff:fe81:655d/64), vethc059d7c (fe80::7819:6aff:fe8e:7f7e/64), vethb8d27ee (fe80::14bd:5bff:fe8d:f9ee/64), vethc9cd1f2 (fe80::387a:84ff:fed8:638d/64), vethde1ac5b (fe80::9098:81ff:fe64:377/64), veth09aa42f (fe80::c888:a4ff:fe5e:46f9/64), vetheebba0a (fe80::bc5d:67ff:fe1d:e908/64) announce_addresses | 192.168.2.10, fd1b:c992:9b6a:208b:7f87:b6d5:93a1:6490, fe80::cf6d:e585:b8f8:8919  </details>  <details><summary>Recorder</summary>  oldest_recorder_run | August 23, 2025 at 12:57 PM -- | -- current_recorder_run | September 1, 2025 at 5:57 PM estimated_db_size | 162.59 MiB database_engine | sqlite database_version | 3.48.0  </details>  <details><summary>SpotifyPlus</summary>  integration_version | v1.0.156 -- | -- clients_configured | 1: François (premium) api_endpoint_reachable | pending  </details>

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

Tractive

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/tractive/

### Diagnostics information

[config_entry-tractive-01K493YXPD9KMDJ1766THJGE9V.json](https://github.com/user-attachments/files/22129202/config_entry-tractive-01K493YXPD9KMDJ1766THJGE9V.json)

### Example YAML snippet

```yaml

```

### Anything in the logs that might be useful for us?

```txt

```

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], [user], [user], mind taking a look at this issue as it has been labeled with an integration (`tractive`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L1628) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `tractive` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign tractive` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[tractive documentation](https://www.home-assistant.io/integrations/tractive)
[tractive source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/tractive)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

I can confirm that, Tractive has stopped sending "wellness" data through its API. If this situation persists, these entities will need to be removed.

### Comment 3 ([user]):

It's a shame they removed it without informing the users.  :(

### Comment 4 ([user]):

Bummer about the removal. It's a shame. :(

### Comment 5 ([user]):

Maybe it's just an error on their side? I can try to contact them if this is still the case in a few days.
I am pessimistic because the data are still working in the app itself.
For what it worth: I stopped receiving data from those sensors on September 1st, around 4am EST.

### Comment 6 ([user]):

Mine went offline at that exact time as well.

On Thu, Sep 4, 2025 at 8:39 AM Peskinator ***@***.***> wrote:

> *Peskinator* left a comment (home-assistant/core#151651)
> <https://github.com/home-assistant/core/issues/151651#issuecomment-3254053360>
>
> Maybe it's just an error on their side? I can try to contact them if this
> is still the case in a few days.
> I am pessimistic because the data are still working in the app itself.
> For what it worth: I stopped receiving data from those sensors on
> September 1st, around 4am EST.
>
> —
> Reply to this email directly, view it on GitHub
> <https://github.com/home-assistant/core/issues/151651#issuecomment-3254053360>,
> or unsubscribe
> <https://github.com/notifications/unsubscribe-auth/AOTSSYMD7WQ3BDBJFSEYBMD3RBFI7AVCNFSM6AAAAACFSJ6R2KVHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZTENJUGA2TGMZWGA>
> .
> You are receiving this because you commented.Message ID:
> ***@***.***>
>

### Comment 7 ([user]):

I have contacted them through a form, but not sure if they will respond the
way we hope for.

On Thu, Sep 4, 2025 at 4:39 PM Peskinator ***@***.***> wrote:

> *Peskinator* left a comment (home-assistant/core#151651)
> <https://github.com/home-assistant/core/issues/151651#issuecomment-3254053360>
>
> Maybe it's just an error on their side? I can try to contact them if this
> is still the case in a few days.
> I am pessimistic because the data are still working in the app itself.
> For what it worth: I stopped receiving data from those sensors on
> September 1st, around 4am EST.
>
> —
> Reply to this email directly, view it on GitHub
> <https://github.com/home-assistant/core/issues/151651#issuecomment-3254053360>,
> or unsubscribe
> <https://github.com/notifications/unsubscribe-auth/AB4G7II5T7OMCUKVNLMPPFT3RBFI7AVCNFSM6AAAAACFSJ6R2KVHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZTENJUGA2TGMZWGA>
> .
> You are receiving this because you commented.Message ID:
> ***@***.***>
>

### Comment 8 ([user]):

> It's a shame they removed it without informing the users.

The integration does not use the official Tractive API (because it does not exist) but their internal one, they do not have to inform anyone about changes.

> Maybe it's just an error on their side?

The integration uses the same API used on the https://my.tractive.com/#/map website. This website doesn't currently display "wellness" information, so I assume this is an intentional change and not a bug.

> I am pessimistic because the data are still working in the app itself.

The mobile app likely uses a different API or has different permissions.

### Comment 9 ([user]):

Unfortunately I think it is intentional, as now this is on their website:

**Some features such as Wellness Monitoring, Augmented Reality and Power Saving Zones are only available in the mobile app.**

### Comment 10 ([user]):

That's a shame -- they have a premium product, it should have premium features.

## PR Review Comments

**[user]** on `homeassistant/components/tractive/__init__.py`:

We can add `trackable_obj.health_overview()` to the `asyncio.gather()` in the line 155:

```python
tracker_details, hw_info, pos_report, health_overview = await asyncio.gather(
        tracker.details(), tracker.hw_info(), tracker.pos_report(), trackable_obj.health_overview()
    ) 
```

**[user]** on `homeassistant/components/tractive/__init__.py`:

```suggestion
    health_overview: dict
```

**[user]** on `homeassistant/components/tractive/__init__.py`:

Tractive has deprecated the `wellness_overview` message (the API no longer sends these messages), we should remove all code related to `wellness_overview`.

**[user]** on `homeassistant/components/tractive/sensor.py`:

You shouldn't combine two types of changes in a single PR. If it's supposed to be a bugfix, it shouldn't add new entities.

BTW, if possible, after the release of the new version of aiotractive, this PR should be split into two parts. One to bump the aiotractive version, the other to migrate sensors to use the new API.

**[user]** on `homeassistant/components/tractive/sensor.py`:

Entities that are not supported by the current API version should be removed in a separate PR. Adding `entity_registry_enabled_default=False` doesn't solve anything.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
