# Home Assistant Recteq Integration

> This was an abandoned fork that was picked up by others including mochman who made some great improvements. However, I needed to modify it to get my RT700 working and I am hoping to add some capabilities and make this integration more robust for most users. I will need feedback to capture the changes though as I only have one grill to test on :)

Custom integration for [recteq][recteq] grills and smokers providing a climate
entity to control the unit and sensor entities for the probes.

[![hacs-badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![issue-badge](https://img.shields.io/github/issues/eclipse1482/recteq)](https://github.com/eclipse1482/recteq/issues)
[![pr-badge](https://img.shields.io/github/issues-pr/eclipse1482/recteq)](https://github.com/eclipse1482/recteq/issues)
[![release-badge](https://img.shields.io/github/v/release/eclipse1482/recteq?sort=semver)](https://github.com/eclipse1482/recteq/releases/latest)
[![commit-badge](https://img.shields.io/github/last-commit/eclipse1482/recteq)](https://github.com/eclipse1482/recteq/commit/main)
[![license-badge](https://img.shields.io/github/license/eclipse1482/recteq)](https://github.com/eclipse1482/recteq/blob/main/LICENSE)
[![commits-badge](https://img.shields.io/github/commits-since/eclipse1482/recteq/latest/main?sort=semver)](https://github.com/eclipse1482/recteq/commits/main)

> **NOTE** - This isn't supported or approved by [recteq][recteq] at all!

![climate](img/climate.png)

![entities](img/entities.png)

## Installation

We recommend you install [HACS](https://hacs.xyz/) first, then add
<https://github.com/eclipse1482/recteq> as a custom integration repository and
finally, add the integration from there.

Instead, if you prefer the manual route, you could download a copy of the
[latest release][latest] and unpack the contents into into
`config/custom_components/recteq/` on your HA machine. Feeling adventurous?
Using `git clone` in `config/custom_components/` to pull the project from
Github works too.

In either case, you need to restart HS once it's installed. Then you need to
[configure](#configuration) it.

## Configuration

This integration is configured using the UI only; no changes in
`configuration.yaml` are needed. Navigate to **Configuration** &raquo;
**Integrations** and tap the red "+" button in the bottom-right. Search for and
select the "Recteq" entry in the list of available integrations to setup.
You'll get the dialog shown below. Enter the details for your grill and tap
"Submit".

![config](img/config.png)

Repeat the process if you have multiple grills to control. _(ps: I'm jealous!)_

See the [wiki](https://github.com/eclipse1482/recteq/wiki) for info in where to get
the IP address, device ID and local key values needed.

The "Force Fahrenheit" option was added for folks who operate HA in Celsius but
cook in Fahrenheit. The climate and sensor entities will report temperatures in Fahrenheit rather than converting them to Celsius when this option is set. The
thermostat card will still display °C but the values will actually be °F.

## User Interface

The stock [Thermostat Card](https://www.home-assistant.io/lovelace/thermostat/)
can be used to present the current state of the recteq when it's on. I like to
hide it and display a button instead when it's off. I use conditionals like
below. The result is shown in the screenshot at that top of this document.

```yaml
type: vertical-stack
cards:
  - type: conditional
    conditions:
      - entity: climate.smoker
        state: 'off'
    card:
      type: glance
      entities:
        - entity: climate.smoker
          tap_action:
            action: toggle
  - type: conditional
    conditions:
      - entity: climate.smoker
        state_not: 'off'
    card:
      type: thermostat
      entity: climate.smoker
  - type: conditional
    conditions:
      - entity: climate.smoker
        state_not: 'off'
      - entity: input_number.smoker_probe_a_target
        state_not: '0.0'
    card:
      type: glance
      entities:
        - entity: sensor.smoker_probe_a_temperature
          name: Probe-A
        - entity: input_number.smoker_probe_a_target
          name: Target
        - entity: sensor.smoker_probe_a_status
          name: Status
      state_color: true
  - type: history-graph
    entities:
      - entity: sensor.smoker_target_temperature
        name: Target
      - entity: sensor.smoker_actual_temperature
        name: Actual
      - entity: sensor.smoker_probe_a_temperature
        name: Probe-A
      - entity: sensor.smoker_probe_b_temperature
        name: Probe-B
    refresh_interval: 0
    hours_to_show: 8
```

The third panel above mimics the logic in the app that monitors the probe. I
created an `input_number` named "Smoker Probe-A Target" (min=0.0, max=500.0,
step=5.0, mode=slider, unit=°F, icon=mdi:thermometer). Then I added the
template sensor below. An automation to send notifications could be added too
if desired.

> **NOTE* - If you're using the "Force Fahrenheit" option, don't set the units
> on the input\_number or HA will try to convert it automagically.

```yaml
sensor:
  - platform: template
    sensors:
      smoker_probe_a_status:
        value_template: >
          {% if states('climate.smoker') == 'off' or states('sensor.smoker_probe_a_temperature') == 'unavailable' -%}
            undefined
          {% else %}
            {% set target = states('input_number.smoker_probe_a_target')|round %}
            {% set actual = states('sensor.smoker_probe_a_temperature')|round %}
            {% set offset = actual - target %}
            {% if offset > 5 %}Over Temp!
            {% elif offset > -5 %}At Target
            {% elif offset > -15 %}Approaching...
            {% else %}Waiting...{% endif %}
          {%- endif %}
```

## Notifications
Paste these scripts into your automations.yaml file. These automations send notifications for various reasons such as turning on your grill, when it is approaching target temperature. When it exceeds or falls far below target temperature. When probes are almost at temperature and at temperature. Etc.
```yaml
- id: '1626129294093'
  alias: Recteq Probe A Alarm - 5F
  description: ''
  triggers:
  - value_template: "{% if states('sensor.rt700_probe_a_temperature') not in ['unavailable','unknown']
      %}\n  {% if float(states.sensor.rt700_probe_a_temperature.state) >= float(states.input_number.probe_a_alarm_temp.state)-5
      %}\n   True\n  {% else %}\n   False\n  {% endif %}\n{% else %}\n False\n{% endif
      %}"
    trigger: template
  conditions:
  - condition: state
    entity_id: input_boolean.probe_a_alarm_set
    state: 'on'
  - condition: numeric_state
    entity_id: input_number.probe_a_alarm_temp
    above: 0
  actions:
  - data:
      message: Probe A is 5 degrees below target temp
      title: Food is Almost Ready
      data:
        channel: recteq
        actions:
        - action: URI
          title: View
          uri: /lovelace/grill
    action: notify.all_devices
  - wait_for_trigger:
    - value_template: "{% if states('sensor.rt700_probe_a_temperature') not in ['unavailable','unknown']
        %}\n  {% if float(states.sensor.rt700_probe_a_temperature.state) < float(states.input_number.probe_a_alarm_temp.state)-5
        %}\n   True\n  {% else %}\n   False\n  {% endif %}\n{% else %}\n False\n{%
        endif %}"
      trigger: template
    - entity_id: sensor.rt700_probe_a_temperature
      to: unavailable
      trigger: state
    continue_on_timeout: false
    timeout: '20:00:00'
  mode: single
- id: '1626131232835'
  alias: Recteq Grill Temperature - 10F
  description: ''
  triggers:
  - value_template: "{% if states('sensor.rt700_actual_temperature') not in ['unavailable','unknown']
      %}\n  {% if float(states.sensor.rt700_actual_temperature.state) >= float(states.sensor.rt700_target_temperature.state)-10
      %}\n   True\n  {% else %}\n   False\n  {% endif %}\n{% else %}\n False\n{% endif
      %}"
    trigger: template
  conditions: []
  actions:
  - data:
      message: Your grill will be ready soon. It is 10 degrees below your target temperature.
      title: Recteq - Heating up!
      data:
        channel: recteq
        actions:
        - action: URI
          title: View
          uri: /lovelace/grill
    action: notify.all_devices
  - wait_for_trigger:
    - value_template: "{% if states('sensor.rt700_actual_temperature') not in ['unavailable','unknown']
        %}\n  {% if float(states.sensor.rt700_actual_temperature.state) < float(states.sensor.rt700_target_temperature.state)-10
        %}\n   True\n  {% else %}\n   False\n  {% endif %}\n{% else %}\n False\n{%
        endif %}"
      trigger: template
      for:
        hours: 0
        minutes: 5
        seconds: 0
    timeout: '20:00:00'
    continue_on_timeout: false
  - data:
      message: Your grill has dropped 10 degrees below your target temperature
      title: Recteq - Grill has cooled!
      data:
        actions:
        - action: URI
          title: View
          uri: /lovelace/grill
        color: red
    action: notify.all_devices
  mode: single
- id: '1626140861013'
  alias: Recteq Grill Temperature + 10F
  description: ''
  triggers:
  - value_template: "{% if states('sensor.rt700_actual_temperature') not in ['unavailable','unknown']
      %}\n  {% if float(states.sensor.rt700_actual_temperature.state) >= float(states.sensor.rt700_target_temperature.state)+10
      %}\n   True\n  {% else %}\n   False\n  {% endif %}\n{% else %}\n False\n{% endif
      %}"
    trigger: template
  conditions: []
  actions:
  - data:
      message: Your grill is 10 degrees above your target temperature
      title: Recteq - Warning!
      data:
        channel: recteq
        actions:
        - action: URI
          title: View
          uri: /lovelace/grill
        color: red
    action: notify.all_devices
  - wait_for_trigger:
    - value_template: "{% if states('sensor.rt700_actual_temperature') not in ['unavailable','unknown']
        %}\n  {% if float(states.sensor.rt700_actual_temperature.state) < float(states.sensor.rt700_target_temperature.state)+10
        %}\n   True\n  {% else %}\n   False\n  {% endif %}\n{% else %}\n False\n{%
        endif %}"
      trigger: template
    continue_on_timeout: false
    timeout: '20:00:00'
  - data:
      message: Your grill is back within 10 degrees of your target temperature
      title: Recteq
      data:
        channel: recteq
        actions:
        - action: URI
          title: View
          uri: /lovelace/grill
    action: notify.all_devices
  mode: single
- id: '1626380331997'
  alias: Recteq Probe B Alarm - 5F
  description: ''
  triggers:
  - value_template: "{% if states('sensor.rt700_probe_b_temperature') not in ['unavailable','unknown']
      %}\n  {% if float(states.sensor.rt700_probe_b_temperature.state) >= float(states.input_number.probe_b_alarm_temp.state)-5
      %}\n   True\n  {% else %}\n   False\n  {% endif %}\n{% else %}\n False\n{% endif
      %}"
    trigger: template
  conditions:
  - condition: state
    entity_id: input_boolean.probe_b_alarm_set
    state: 'on'
  - condition: numeric_state
    entity_id: input_number.probe_b_alarm_temp
    above: 0
  actions:
  - data:
      message: Probe B is 5 degrees below target temp
      title: Food is Almost Ready
      data:
        channel: recteq
        actions:
        - action: URI
          title: View
          uri: /lovelace/grill
    action: notify.all_devices
  - wait_for_trigger:
    - value_template: "{% if states('sensor.rt700_probe_b_temperature') not in ['unavailable','unknown']
        %}\n  {% if float(states.sensor.rt700_probe_b_temperature.state) < float(states.input_number.probe_b_alarm_temp.state)-5
        %}\n   True\n  {% else %}\n   False\n  {% endif %}\n{% else %}\n False\n{%
        endif %}"
      trigger: template
    - entity_id: sensor.rt700_probe_b_temperature
      to: unavailable
      trigger: state
    continue_on_timeout: false
    timeout: '20:00:00'
  mode: single
- id: '1626380349717'
  alias: Recteq Probe B Alarm
  description: ''
  triggers:
  - value_template: "{% if states('sensor.rt700_probe_b_temperature') not in ['unavailable','unknown']
      %}\n  {% if float(states.sensor.rt700_probe_b_temperature.state) >= float(states.input_number.probe_b_alarm_temp.state)
      %}\n   True\n  {% else %}\n   False\n  {% endif %}\n{% else %}\n False\n{% endif
      %}"
    trigger: template
  conditions:
  - condition: state
    entity_id: input_boolean.probe_b_alarm_set
    state: 'on'
  - condition: numeric_state
    entity_id: input_number.probe_b_alarm_temp
    above: 0
  actions:
  - data:
      message: 'Probe B is at target temp '
      title: Food is Done!
      data:
        channel: recteq
        actions:
        - action: URI
          title: View
          uri: /lovelace/grill
        color: red
    action: notify.all_devices
  - wait_for_trigger:
    - value_template: "{% if states('sensor.rt700_probe_b_temperature') not in ['unavailable','unknown']
        %}\n  {% if float(states.sensor.rt700_probe_b_temperature.state) < float(states.input_number.probe_b_alarm_temp.state)
        %}\n   True\n  {% else %}\n   False\n  {% endif %}\n{% else %}\n False\n{%
        endif %}"
      trigger: template
    - entity_id: sensor.rt700_probe_b_temperature
      to: unavailable
      trigger: state
    continue_on_timeout: false
    timeout: '20:00:00'
  mode: single
- id: '1626380490549'
  alias: Recteq Probe A Alarm
  description: ''
  triggers:
  - value_template: "{% if states('sensor.rt700_probe_a_temperature') not in ['unavailable','unknown']
      %}\n  {% if float(states.sensor.rt700_probe_a_temperature.state) >= float(states.input_number.probe_a_alarm_temp.state)
      %}\n   True\n  {% else %}\n   False\n  {% endif %}\n{% else %}\n False\n{% endif
      %}"
    trigger: template
  conditions:
  - condition: state
    entity_id: input_boolean.probe_a_alarm_set
    state: 'on'
  - condition: numeric_state
    entity_id: input_number.probe_a_alarm_temp
    above: 0
  actions:
  - data:
      message: Probe A is at target temp
      title: Food is Done!
      data:
        channel: recteq
        actions:
        - action: URI
          title: View
          uri: /lovelace/grill
        color: red
    action: notify.all_devices
  - wait_for_trigger:
    - value_template: "{% if states('sensor.rt700_probe_a_temperature') not in ['unavailable','unknown']
        %}\n  {% if float(states.sensor.rt700_probe_a_temperature.state) < float(states.input_number.probe_a_alarm_temp.state)
        %}\n   True\n  {% else %}\n   False\n  {% endif %}\n{% else %}\n False\n{%
        endif %}"
      trigger: template
    - trigger: state
      entity_id:
      - sensor.rt700_probe_a_temperature
      to: unavailable
    continue_on_timeout: false
    timeout: '20:00:00'
  mode: single
- id: '1626739464825'
  alias: Recteq Grill at Temperature
  description: ''
  triggers:
  - value_template: "{% if states('sensor.rt700_actual_temperature') not in ['unavailable','unknown']
      %}\n {% if float(states.sensor.rt700_actual_temperature.state) >= float(states.sensor.rt700_target_temperature.state)
      %}\n  True\n {% else %}\n  False\n {% endif %}\n{% else %}\n False\n{% endif
      %}"
    trigger: template
  conditions: []
  actions:
  - data:
      message: Your grill is at your target temperature
      title: Recteq Ready!
      data:
        channel: recteq
        actions:
        - action: URI
          title: View
          uri: /lovelace/grill
        sticky: false
    action: notify.all_devices
  - wait_for_trigger:
    - value_template: "{% if states('sensor.rt700_actual_temperature') not in ['unavailable','unknown']
        %}\n  {% if float(states.sensor.rt700_actual_temperature.state) < float(states.sensor.rt700_target_temperature.state)
        - 50 %}\n   True\n  {% else %}\n   False\n  {% endif %}\n{% else %}\n False\n{%
        endif %}"
      trigger: template
    continue_on_timeout: false
    timeout: '20:00:00'
  mode: single
```

## Change Log

* _future_
* 1.0.0
  * Fix error for async_forward_entry_setup being deprecated 
  * Add low and full modes
* 0.2.1
  * Fixing DPS for RT700
  * Fixed Tuya Protocol 3.4 and ability for Local Key to use more the hex digits for new controllers
  * Fixed issue that caused Home Assistant to slow down significantly when integration was enabled, but grill was offline
  * Adding drop down to select Tuya Protocol and Grill Type which will dynamically point the correct data points to probe names (I will need help to make sure I align them correctly so this will be a work in progress)
  * Fixed Device Key Length
  * Fixed Probe Temps
  * Switched to tintuya for data reading
* 0.0.4
  * Metric units support
  * Force-Fahrenheit option
* 0.0.3 
  * Added target & actual sensors
  * Sensors and current temperature report "unavailable" when off.
  * Added UI usage to README
  * Bugfixes and cleanup.
* 0.0.2 
  * HACS support
  * README additions
* 0.0.1 
  * Initial release candidate
  * Works for me. Looking for others to test.

## License

MIT

See [LICENSE](LICENSE) for details.

## Support

Submit [issues](https://github.com/mochman/recteq/issues) for defects, feature
requests or questions. I'll try to help as I can.

I am *very* interested in feedback on this to know whether it's working for
others.

## Credits

This is forked from mochman (https://github.com/mochman) who forked the repo by Paul Dugas, <paul@dugas.cc>.

Paul Dugas learned this was possible from [`SDNick484/rectec_status`][rectec_status] and
based the intial versions of the project on his examples. Much thanks to
[mochman](https://github.com/mochman/),
[SDNick](https://github.com/SDNick484/) along with those he credits;
[codetheweb](https://github.com/codetheweb/),
[clach04](https://github.com/clach04),
[blackrozes](https://github.com/blackrozes),
[jepsonrob](https://github.com/jepsonrob), and all the other contributors on
tuyapi and python-tuya who have made communicating to Tuya devices possible
with open source code.

[recteq]: https://www.recteq.com/
[latest]: https://github.com/mochman/recteq/releases/latest
[rectec_status]: https://github.com/SDNick484/rectec_status
