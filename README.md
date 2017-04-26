### Pre alpha development
Please note that orangengine is still considered pre alpha and has not made a public release yet.
Soon...

Also note that the project is currently using a custom fork of the pandevice library located [here](https://github.com/lampwins/pandevice)
You will need to clone this fork and install it manually to satisfy the pandevice requirement until such a time as the new functionality
is added to pandevice proper (PRs currently open).

# orangengine
Firewall Policy Automation Engine

Orangengine is a [netmiko](https://github.com/ktbyers/netmiko)/[napalm](https://github.com/napalm-automation/napalm)
like library for working with network firewall policy.

Currently we support these platforms:
- Juniper SRX
- Palo Alto Networks - Panorama Device Groups
- VMware NSX DFW (road map)

Orangengine works by connecting to a device and parsing its policy into a common
data model. This allows us to interact with the policy in an abstracted, vendor
neutral manner. Here is a simple example of a policy representation in orangengine:
```
my_policy = {
    'source_addresses': ['10.0.0.1/32', '10.20.0.2/32'],
    'destination_addresses': ['10.50.0.1/32'],
    'services': [('tcp', '443'), ('tcp', '22')],
    'action': 'permit'
}
```

# Getting Started
First we will need to define the parameters needed to make a device connection.
```
device_params = {
    'device_type': 'juniper_srx',
    'ip': '192.168.188.2',
    'username': 'admin',
    'password': 'admin',
}
```
`device_type` defines what kind of device we are connecting to so we use the
appropriate driver. Generally there is a common set of params among the device drivers
such as `username`, `password`, etc. Some drivers have support for other parameters,
for example you can connect to a Palo Alto Networks device using an `api_key`.

Now we can dispatch our device connection using our parameter dictionary.
```
device = orangengine.dispatch(**device_params)
```
This will return us an instance of our device object using the given driver and by
default will open a connection to the device and parse the entire policy base.

At this point with a fully parsed policy, we can do a number things like search the
policy base or request a candidate for a new policy or policy addition. Let's look at
a simple policy search (called a policy match) example.

Using the policy model described above, lets find all policies that have `10.0.0.1/32`
as a destination with an action of permit.

```
match_criteria = {
    'destination_addresses': ['10.0.0.1/32'],
    'action': 'permit',
}
```
Now we use the most basic matching function to search the policy base and return a list
of matched policies.
```
matched_policies = device.policy_match(match_criteria, match_containing_networks=False)
```
As you can see, by default `policy_match()` will search contianing networks. Meaning in this example,
we would have gotten result for polciies containing `10.0.0.0/24` if `match_containing_networks` was true.

Finally, we can simply print the matched policy names.
```
for p in matched_policies:
    print p.name
```
