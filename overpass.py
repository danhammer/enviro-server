import json
import re


def in_polygon(point, poly):
    """Accepts a point [lon, lat] and a polygon [[lon1, lat1], [lon2, lat2],
    ...] and determines whether the point is within the supplied polygon.
    Returns a boolean."""
    x, y = point
    n = len(poly)
    inside = False

    p1x, p1y = poly[0]
    for i in range(n+1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def _osm_prefix(out='json', timeout=25):
    """Generate the OSM prefix with reasonable defaults. Supports no timeout
    by supplying None to this function wrapper."""
    if timeout is not None:
        return '[out:%s][timeout:%s];' % (out, timeout)
    else:
        return '[out:%s];' % out


def _osm_component(geotype, lat, lon, search_pairs, buf=20):
    """Returns the part of the OSM query that filters the type and search
    filters.
    Args:
        geotype: 'node', 'way', or 'relation'
        kv_pairs: {'note': Walmart, 'landuse': Industrial}
    """
    nearby = '(around:%s,%s,%s)' % (float(buf), lat, lon)
    if search_pairs == {}:
        query = geotype + nearby + ';'
    else:
        fields = ['["%s"~"%s"]' % (k, v) for k, v in search_pairs.items()]
        field_str = ''.join(fields)
        query = geotype + field_str + nearby + ';'

    return query + 'out geom;'


def way_to_geojson(way):
    """Accepts a JSON formatted OSM way and returns the geojson representation
    of the object."""
    coords = [[c['lon'], c['lat']] for c in way['geometry']]
    bbox = {
        'xmin': way['bounds']['minlon'],
        'xmax': way['bounds']['maxlon'],
        'ymin': way['bounds']['minlat'],
        'ymax': way['bounds']['minlat']
    }

    try:
        tags = way['tags']
    except KeyError:
        tags = None

    return {
        'type': 'Feature',
        'geometry': {
            'type': 'Polygon',
            'coordinates': [coords]
        },
        'properties': {
            'tags': tags,
            'bounds': bbox
        }
    }


def fetch_overpass(base, payload={}):
    """Accepts a base URL and a payload for a GET request to the overpass API,
    which accepts a strange and very rigid format."""
    if payload == {}:
        url = base
    else:
        param_list = ["%s=%s" % (k, v) for k, v in payload.items()]
        url = re.sub(" ", "%20", base + '?' + '&'.join(param_list))

    try:
        from google.appengine.api import urlfetch
        res = urlfetch.fetch(url).content
        return json.loads(res)
    except ImportError:
        import requests
        res = requests.get(url)
        return res.json()


def in_bbox(point, geojson):
    x, y = point
    bbox = geojson['properties']['bounds']
    res = False
    if (x >= bbox['xmin']):
        if (x <= bbox['xmax']):
            if (y >= bbox['ymin']):
                if (y <= bbox['ymax']):
                    res = True
    return res


def harvest(lat, lon, buf, strict=True, search_pairs={}):
    """ """
    base = "http://overpass-api.de/api/interpreter"
    comps = _osm_component('way', lat, lon, search_pairs=search_pairs, buf=buf)
    data = fetch_overpass(base, payload={'data': _osm_prefix() + comps})
    polys = [way_to_geojson(way) for way in data['elements']]
    if strict:
        polys = filter(lambda x: in_bbox([lon, lat], x), polys)
    return {'results': polys, 'count': len(polys)}
