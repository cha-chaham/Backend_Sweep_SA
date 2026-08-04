import re
import urllib.request

def parse_google_maps_url(url: str):
    try:
        if "goo.gl" in url or "maps.app.goo.gl" in url:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as response:
                url = response.url

        lat, lon = None, None
        match_at = re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", url)
        if match_at:
            lat, lon = float(match_at.group(1)), float(match_at.group(2))
        else:
            match_q = re.search(r"[?&](?:q|ll)=(-?\d+\.\d+),(-?\d+\.\d+)", url)
            if match_q:
                lat, lon = float(match_q.group(1)), float(match_q.group(2))

        return lat, lon
    except Exception:
        return None, None