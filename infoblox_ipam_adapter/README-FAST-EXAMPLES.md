# Example FAST provider usage and template snippets

## FAST provider registration (BIG-IP)

```bash
curl -sku admin:password \
  -X POST https://<bigip>/mgmt/shared/fast/ipam/providers \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "infoblox",
    "providerType": "rest",
    "endpoint": "https://infoblox-adapter.local:8443/ipam"
  }'
```

## FAST template snippet using external provider

```yaml
variables:
  vip_address: "{{ FAST.ipamAllocate('10.1.10.0/24', 'infoblox') }}"
  pool_members: |
    {% set members = [] %}
    {% for i in range(0, member_count) %}
      {% set member_ip = FAST.ipamAllocate('10.2.20.0/24', 'infoblox') %}
      {% do members.append({'serverAddresses': [member_ip], 'servicePort': 8080}) %}
    {% endfor %}
    {{ members }}
```

Note: when FAST calls the external provider it may POST JSON like `{ "network": "10.1.10.0/24", "count": 1 }` and expects a response like `{"addresses": ["10.1.10.5"]}`.
