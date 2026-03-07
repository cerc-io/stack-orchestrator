#!/bin/bash
# /etc/network/if-up.d/ashburn-routing
# Restore policy routing for Ashburn validator relay after reboot/interface up.
# Only act when doublezero0 comes up.

[ "$IFACE" = "doublezero0" ] || exit 0

# Ensure rt_tables entry exists
grep -q '^100 ashburn$' /etc/iproute2/rt_tables || echo "100 ashburn" >> /etc/iproute2/rt_tables

# Add policy rule (idempotent — ip rule skips duplicates silently on some kernels)
ip rule show | grep -q 'fwmark 0x64 lookup ashburn' || ip rule add fwmark 100 table ashburn

# Add default route via mia-sw01 through doublezero0 tunnel
ip route replace default via 169.254.7.6 dev doublezero0 table ashburn

# Add Ashburn IP to loopback (idempotent)
ip addr show lo | grep -q '137.239.194.65' || ip addr add 137.239.194.65/32 dev lo
