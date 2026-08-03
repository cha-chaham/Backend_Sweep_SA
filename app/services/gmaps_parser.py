import re
import urllib.request

def parse_google_maps_url(url: str):
    try:
        # Jika menggunakan link pendek (maps.app.goo.gl atau goo.gl), ikuti redirect-nya
        if "goo.gl" in url or "maps.app.goo.gl" in url:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req) as response:
                url = response.url

        # Pola 1: Format /@lat,lon (Contoh: /@-0.8917,119.8707,17z)
        match_at = re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", url)
        if match_at:
            return float(match_at.group(1)), float(match_at.group(2))

        # Pola 2: Format parameter q=lat,lon atau ll=lat,lon
        match_q = re.search(r"[?&](?:q|ll)=(-?\d+\.\d+),(-?\d+\.\d+)", url)
        if match_q:
            return float(match_q.group(1)), float(match_q.group(2))

        return None, None
    except Exception:
        return None, None