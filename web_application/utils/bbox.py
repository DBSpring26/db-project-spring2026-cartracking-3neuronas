def parse_bbox_string(s: str):
    try:
        parts = [float(x.strip()) for x in s.split(",")]
        if len(parts) == 4:
            return tuple(parts)
    except:
        pass
    return None


def format_bbox(t: tuple) -> str:
    return f"{t[0]},{t[1]},{t[2]},{t[3]}"


def bbox_from_draw_output(draw_data: dict):
    try:
        features = draw_data.get("all_drawings") or []
        if not features:
            return None
        coords = features[0]["geometry"]["coordinates"][0]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        return (min(lons), min(lats), max(lons), max(lats))
    except:
        return None
