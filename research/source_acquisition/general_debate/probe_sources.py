#!/usr/bin/env python3
"""Read-only diagnostics for two published source endpoints. No text downloaded or logged."""
from __future__ import annotations

import json
from urllib.parse import urlparse
import urllib.error
import urllib.request

from acquire import CORPUS_METADATA_URL, CORPUS_URL, OFFICIAL_URL


def probe(label: str, url: str) -> dict:
    # HEAD for data files only; JSON GET is bounded to 2 MiB and reports metadata.
    method = "GET" if label == "harvard_dataset_metadata" else "HEAD"
    headers = {"User-Agent": "UNGA81-historical-data-audit/0.1", "Accept": "application/json"
               if method == "GET" else "*/*"}
    request = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            result = {"label": label, "http_status": response.status,
                      "content_type": response.headers.get("Content-Type"),
                      "content_length": response.headers.get("Content-Length"),
                      "redirected_host": urlparse(response.geturl()).hostname}
            if method == "GET":
                payload = response.read(2_000_001)
                if len(payload) > 2_000_000:
                    result["metadata_status"] = "too_large_to_verify"
                else:
                    try:
                        dataset = json.loads(payload)["data"]["latestVersion"]
                        relevant = []
                        for entry in dataset.get("files", []):
                            df = entry.get("dataFile", {})
                            name = str(df.get("filename", ""))
                            if "UNGDC" in name or "speaker" in name.lower():
                                relevant.append({"id": df.get("id"), "name": name,
                                                 "bytes": df.get("filesize"),
                                                 "checksum": df.get("checksum")})
                        result["dataset_version"] = [dataset.get("versionNumber"),
                                                     dataset.get("versionMinorNumber")]
                        result["candidate_datafiles"] = relevant[:20]
                    except (KeyError, ValueError, TypeError):
                        result["metadata_status"] = "nonconforming_json"
            return result
    except urllib.error.HTTPError as e:
        return {"label": label, "http_status": e.code,
                "reason": "endpoint_returned_error_no_content_read"}
    except (OSError, urllib.error.URLError) as e:
        return {"label": label, "http_status": None,
                "reason": "network_or_TLS_error_" + type(e).__name__}


if __name__ == "__main__":
    print(json.dumps([
        probe("harvard_dataset_metadata", CORPUS_METADATA_URL),
        probe("harvard_pinned_datafile", CORPUS_URL),
        probe("undl_speaker_index", OFFICIAL_URL)
    ], sort_keys=True))
