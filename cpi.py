import ee
import config # TODO remove after intial development
from datetime import datetime


def stats(poly, img, scale=30):
    """Returns"""
    mu = img.reduceRegion(ee.Reducer.mean(), poly, scale)
    stdev = img.reduceRegion(ee.Reducer.stdDev(), poly, scale)
    res = {'mean': mu, 'stdev': stdev, 'area': poly.area()}
    return ee.Feature(None, res)


def cpi_stats(img, inner, outer):
    """Returns the CPI stats for a given image and inner/outer partition of
    the CPI field.  No image calculations are realized, since the function
    will be mapped across an image collection."""
    msecs = img.get('system:time_start')

    instat = stats(inner, img)
    outstat = stats(outer, img)
    return ee.Feature(None, {
        'msecs': msecs,
        'inner': instat,
        'outer': outstat
    })


def cpi_calc(bbox, begin, end, coll_name='LANDSAT/LE7_L1T_32DAY_EVI'):
    """Given a bounding box, return the calculations relevant to Central Pivot
    Irrigation analysis for each image in the series.  The """
    coll = ee.ImageCollection(coll_name)
    rect = ee.Geometry.Rectangle(
        bbox['xmin'], bbox['ymin'], bbox['xmax'], bbox['ymax']
    )

    # Calculate the inner circle and remaining (outer) of the CPI field
    pt = rect.centroid()
    radius = rect.perimeter().divide(7.9)
    buf = pt.buffer(radius)
    outer = rect.difference(buf, 0.05)
    inner = rect.intersection(buf, 0.05)

    def _process(ee_res):
        """Convert the Earth Engine results into a cleaned dictionary for a
        JSON dump and calculations"""
        inner = ee_res['properties']['inner']['properties']
        outer = ee_res['properties']['outer']['properties']
        secs = ee_res['properties']['msecs']/1000
        date = datetime.fromtimestamp(secs).strftime("%Y-%m-%d")
        inner_dict = dict(
            area=inner['area'],
            mu=inner['mean']['EVI'],
            stdev=inner['stdev']['EVI']
        )
        outer_dict = dict(
            area=outer['area'],
            mu=outer['mean']['EVI'],
            stdev=outer['stdev']['EVI']
        )
        return dict(inner=inner_dict, outer=outer_dict, date=date)

    # Map `_process` across the image collection, process the results into a
    # JSON-ready dictionary
    fcoll = coll.filterBounds(rect).filterDate(begin, end)
    ee_results = fcoll.map(lambda x: cpi_stats(x, inner, outer)).getInfo()
    res = [_process(x) for x in ee_results['features']]

    return {'begin': begin, 'end': end, 'results': res, 'count': len(res)}
