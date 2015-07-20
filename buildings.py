import overpass
from geojson import Feature, Polygon


def bbox_query(geotype, bbox, timeout=250):
    """Returns the part of the OSM query that grabs all elements of the
    supplied geotype within the given bounding box.

    Args:
        - geotype (string) 'node', 'way', or 'relation'
        - bbox (dict) standard bbox dictionary
        - timout (int, optional) number of seconds for query before timeout
    """
    prefix = "[out:json][timeout:%s];" % timeout
    bounds = [bbox['ymin'], bbox['xmin'], bbox['ymax'], bbox['xmax']]
    coords = ','.join([str(b) for b in bounds])
    geom = "%s(%s);" % (geotype, coords)
    suffix = "out geom;>;out skel qt;"
    return prefix + geom + suffix


def _water(way):
    """Accepts an OSM way and returns true if the way represents a polygon,
    rather than a point or line."""
    try:
        # If there are duplicate coordinates, then the geometry is closed
        # (read: it is a polygon)
        coords = [(g['lon'], g['lat']) for g in way['geometry']]
        seen = set()
        uniq = []
        for x in coords:
            if x not in seen:
                uniq.append(x)
                seen.add(x)

        building = 'water' in way['tags'].values()

        if len(uniq) != len(coords):
            return building
        else:
            return False

    except KeyError:
        # If there is no `geometry` key then it is likely a node, but
        # certainly not a polygon
        return False


def way_to_geojson(way_poly, bbox=None):
    """Accepts a polygon that remains formatted as an OSM way and converts it
    into a geojson feature."""
    coords = []

    if bbox is not None:
        # Clip the OSM geojsons to the extent of the bounding box, rather than
        # completing the features despite the bounding box
        for g in way_poly['geometry']:
            if g['lon'] < bbox['xmin']:
                x = bbox['xmin']
            elif g['lon'] > bbox['xmax']:
                x = bbox['xmax']
            else:
                x = g['lon']

            if g['lat'] < bbox['ymin']:
                y = bbox['ymin']
            elif g['lat'] > bbox['ymax']:
                y = bbox['ymax']
            else:
                y = g['lat']

            coords.append([x, y])

    else:
        coords = [(g['lon'], g['lat']) for g in way_poly['geometry']]

    try:
        tags = way_poly['tags']
    except KeyError:
        tags = None

    x = Feature(geometry=Polygon(coords), properties=tags, id=way_poly['id'])
    return dict(x)


def harvest(bbox):
    """Harvest building for the supplied bounding box and resolution. TODO:
    Ensure that the resolution is the correct way to do this, given that the
    resolution may be different for the x- and y-directions.
    """
    base = 'http://overpass-api.de/api/interpreter'
    params = {'data': bbox_query('way', bbox)}
    data = overpass.fetch_overpass(base, payload=params)
    polys = filter(_water, data['elements'])
    geos = [way_to_geojson(p) for p in polys]
    return geos
