import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List
import logging

logger = logging.getLogger("infoblox-client")


class InfobloxError(Exception):
    pass


class InfobloxClient:
    def __init__(self, settings):
        self.base = settings.infoblox_url.rstrip('/')
        self.auth = (settings.infoblox_user, settings.infoblox_pass)
        self.verify = settings.infoblox_verify
        self.timeout = settings.request_timeout

        self.session = requests.Session()
        # Optional client cert (tuple of (cert, key) or single pem)
        if settings.infoblox_client_cert and settings.infoblox_client_key:
            self.session.cert = (settings.infoblox_client_cert, settings.infoblox_client_key)
        elif settings.infoblox_client_cert:
            self.session.cert = settings.infoblox_client_cert

        # Retry strategy for transient errors
        retries = Retry(total=3, backoff_factor=0.5,
                        status_forcelist=(502, 503, 504), allowed_methods=("GET","POST","DELETE","PUT","PATCH"))
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def allocate_ips(self, network: str, count: int = 1, hostname: str | None = None) -> List[str]:
        """Allocate one or more IPs using Infoblox next_available_ip function and then create host record(s).
        network may be a CIDR (e.g. 10.1.10.0/24) or an Infoblox network ref like network/Z_10.1.10.0/24.
        """
        # 1) call next_available_ip
        url = f"{self.base}/network/{network}/_function/next_available_ip" if not network.startswith("/network") else f"{self.base}{network}/_function/next_available_ip"
        payload = {"num": count}
        logger.debug("Requesting next_available_ip %s -> %s", url, payload)
        r = self.session.post(url, json=payload, auth=self.auth, verify=self.verify, timeout=self.timeout)
        if r.status_code not in (200, 201):
            raise InfobloxError(f"next_available_ip failed: {r.status_code} {r.text}")
        data = r.json()
        # WAPI returns ips in different shapes depending on version; try common patterns
        ips = []
        if isinstance(data, dict) and 'ips' in data:
            ips = data['ips']
        elif isinstance(data, list):
            # some versions return list of strings
            ips = data
        elif isinstance(data, dict) and 'result' in data and isinstance(data['result'], list):
            ips = data['result']
        else:
            # fallback: try to extract any ip-looking strings
            raise InfobloxError(f"Unexpected next_available_ip response: {data}")

        created = []
        # 2) optionally create host record(s) to reserve
        for idx, ip in enumerate(ips):
            hname = hostname if hostname else None
            if count > 1 and hostname:
                hname = f"{hostname}-{idx+1}"
            if hname:
                payload = {"name": hname, "ipv4addrs": [{"ipv4addr": ip}]}
                r2 = self.session.post(f"{self.base}/record:host", json=payload, auth=self.auth, verify=self.verify, timeout=self.timeout)
                if r2.status_code not in (200, 201):
                    # If we fail to create host record, attempt to cleanup previously created records
                    logger.error("Failed to create host record for %s: %s", ip, r2.text)
                    raise InfobloxError(f"Failed to create host record: {r2.status_code} {r2.text}")
            created.append(ip)
        return created

    def release_ip(self, ip: str):
        """Release an IP by deleting the host record associated with it (if exists).
        Returns the WAPI _ref of deleted object or a message if none found.
        """
        # find any host records with that IP
        r = self.session.get(f"{self.base}/record:host", params={"ipv4addr": ip}, auth=self.auth, verify=self.verify, timeout=self.timeout)
        if r.status_code != 200:
            raise InfobloxError(f"Failed to query host records: {r.status_code} {r.text}")
        data = r.json()
        if not data:
            # nothing to delete; consider it released
            return {"message": "no host record found"}
        # delete all matching records
        results = []
        for rec in data:
            ref = rec.get('_ref')
            if not ref:
                continue
            r2 = self.session.delete(f"{self.base}/{ref}", auth=self.auth, verify=self.verify, timeout=self.timeout)
            if r2.status_code not in (200, 201, 204):
                logger.error("Failed to delete %s: %s", ref, r2.text)
                raise InfobloxError(f"Failed to delete record {ref}: {r2.status_code} {r2.text}")
            results.append(ref)
        return {"deleted": results}

    def list_networks(self):
        r = self.session.get(f"{self.base}/network", auth=self.auth, verify=self.verify, timeout=self.timeout)
        if r.status_code != 200:
            raise InfobloxError(f"Failed to list networks: {r.status_code} {r.text}")
        return r.json()
