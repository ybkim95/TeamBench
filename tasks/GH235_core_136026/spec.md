# GH235_core_136026: Set  clean_start=True on connect to MQTT broker — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/135443
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

### Issue Description: Inconsistent MQTT Persistent Session Settings in Home Assistant

#### Description:

The MQTT component in Home Assistant demonstrates inconsistent and contradictory handling of persistent session settings on reconnect, depending on the MQTT protocol version used.

- **MQTT 3.1.1**:  
  - The `clean session` flag is set to `1`, which disables persistent sessions.  
  - This behavior is consistent with not using persistent sessions.

- **MQTT 5**:  
  - The `clean start` flag is set to `0`, which enables persistent sessions.  
  - However, the `sessionExpiry` interval is set to `0`, which negates the use of persistent sessions by immediately deleting the session upon network disconnection as defined by the [MQTT 5 Specification](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901048).

#### Expected Behavior:
Persistent session handling should be consistent across MQTT versions and logically coherent:
1. If persistent sessions are not intended:
   - Set `clean session` (MQTT 3.1.1) to `1` and `clean start` (MQTT 5) to `1`.
2. If persistent sessions are intended:
   - Set `clean session` (MQTT 3.1.1) to `0` and `clean start` (MQTT 5) to `0`.
   - Set a **non-zero** `sessionexpiry` interval to preserve sessions after disconnection.

#### Actual Behavior:
- **MQTT 3.1.1**: Persistent sessions are correctly disabled with `cleansession=1`.  
- **MQTT 5**:  
  - `clean start` is set to `0`, enabling persistent sessions.  
  - At the same time, the `sessionexpiry` interval is set to `0`, which contradicts the persistent session configuration by causing sessions to be deleted upon disconnection.

#### Proposed Resolution:
1. Ensure consistent and logical handling of session persistence across MQTT versions:
   - **Option 1**: Disable persistent sessions:
     - Set `cleansession=1` (MQTT 3.1.1) and `cleanstart=1` (MQTT 5).
   - **Option 2**: Enable persistent sessions correctly:
     - Set `cleansession=0` (MQTT 3.1.1) and `cleanstart=0` (MQTT 5).
     - Set `sessionexpiry` to a **non-zero** value for MQTT 5.

#### Steps to Reproduce:
1. Configure the MQTT component in Home Assistant.  
2. Connect using an MQTT 3.1.1 client and observe that persistent sessions are disabled (`cleansession=1`).  
3. Connect using an MQTT 5 client and perform server side disconnect.
4. The client will reconnect and you can observe the conflicting session settings:
   - `cleanstart=0` (persistent sessions enabled).
   - `sessionexpiry=0` (sessions deleted on disconnection).  

#### Additional Notes:
This inconsistency can cause unexpected behavior when switching between MQTT versions or when clients rely on persistent sessions for state preservation. Aligning the configuration logic is essential for predictable and reliable operation.

### What version of Home Assistant Core has the issue?

2025.1.2

### What was the last working version of Home Assistant Core?

2025.1.2

### What type of installation are you running?

Home Assistant Core

### Integration causing the issue

MQTT

### Link to integration documentation on our website

_No response_

### Diagnostics information

_No response_

### Example YAML snippet

_No response_

### Anything in the logs that might be useful for us?

_No response_

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Additionally to what is described above:

Using persistent sessions could be useful as it bring messages queuing for messages sent with QoS greater then zero. This would bring additional resilience as HA would be able to process messages that have been sent during HA downtime.

### Comment 2 ([user]):

![image](https://github.com/user-attachments/assets/8581599f-d714-4d8c-9562-042df91da561)
![image](https://github.com/user-attachments/assets/1e68598c-f7ca-4103-9ab4-040614982dbf)
![image](https://github.com/user-attachments/assets/1550aa9f-5080-4eb0-84aa-bcc09986fa1a)

### Comment 3 ([user]):

After further investigation a possible cause for this behavior is located in the Paho MQTT client library:

```python
# For MQTT V5, use the clean start flag only on the first successful connect
MQTT_CLEAN_START_FIRST_ONLY: CleanStartOption = 3
```

and 

```python
connect_flags = 0
        if self._protocol == MQTTv5:
            if self._clean_start is True:
                connect_flags |= 0x02
            elif self._clean_start == MQTT_CLEAN_START_FIRST_ONLY and self._mqttv5_first_connect:
                connect_flags |= 0x02
        elif self._clean_session:
            connect_flags |= 0x02
```

As the HA MQTT component does not explicitly define `clean_start` the above shown code will use `clean_start=true` on first connect and `clean_start=false` on reconnect for the same client instance. This is coherent with the above described findings.

### Comment 4 ([user]):

Hey there [user], [user], [user], mind taking a look at this issue as it has been labeled with an integration (`mqtt`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L968) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `mqtt` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign mqtt` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[mqtt documentation](https://www.home-assistant.io/integrations/mqtt)
[mqtt source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/mqtt)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 5 ([user]):

As for now, persistent connections are not intended. So according to your information we should update the MQTT client settings for version 5.0. It could be an improvement though to support persistent sessions in the future, so that is something to look in deeper.

### Comment 6 ([user]):

[user] do you want to start a PR your self to fix the consistency for v5 connections, or do you want me to open a PR?

### Comment 7 ([user]):

[user] I created a PR as you can see above.

## PR Review Comments

**[user]** on `homeassistant/components/mqtt/client.py`:

I think we should pass `clean_start` as a keyword argument so we don't have to pass possibly changing defaults for `bind_address` and `bind_port`.

**[user]** on `homeassistant/components/mqtt/client.py`:

Yes, makes sense. [user] how could this be done in the context of using async executor jobs? It seems to use positional arguments...

**[user]** on `homeassistant/components/mqtt/client.py`:

[user] if you like, may be I can help you with the test? In that case you'll need to sign the CLA.

**[user]** on `homeassistant/components/mqtt/client.py`:

[user] this would be awesome. CLA signed!

**[user]** on `homeassistant/components/mqtt/client.py`:

[user] can you support? How could `clean_start` be passed as a keyword argument?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
