import config
import ee
import ast
from datetime import datetime


def acqtime(feature):
    # A handler that returns the correctly formatted date, based on asset.
    msec = feature['properties']['system:time_start']
    return datetime.fromtimestamp(msec/1000).isoformat()


def id_stack(coll, begin, end):
    # Returns the a dictionary with the acquisition date as the key and the
    # asset IDs as the value, all for the image collection between the two
    # supplied dates in YYYY-MM-DD format.
    stack = coll.filterDate(begin, end).getInfo()['features']
    return [dict(date=acqtime(x), id=x['id']) for x in stack]


def _summary(img, geom, scale=30):
    # Accepts a GEE image and a GEE geometry.  Returns the mean and standard
    # deviation of the EVI values within the geometry at 30m resolution.
    mean = img.reduceRegion(ee.Reducer.mean(), geom, scale)
    stdev = img.reduceRegion(ee.Reducer.stdDev(), geom, scale)
    return mean.getInfo()['EVI'], stdev.getInfo()['EVI']


def _process(id_dict, geom):
    # Accepts a dictionary that contains the image ID and date.  Reutrns a
    # dictionary to be directly inserted into the API query results.
    img = ee.Image(id_dict['id'])
    mean, stdev = _summary(img, geom)
    return dict(mean=mean, stdev=stdev, date=id_dict['date'])


def grab(coords, begin, end):
    # Accepts the coordinates as a string, the beginning and end dates in
    # YYYY-MM-DD format.  Returns a dictionary with the EVI summary results,
    # along with the count of observations.
    coll = ee.ImageCollection('LE7_L1T_32DAY_EVI')
    stack = id_stack(coll, begin, end)
    geom = ee.Geometry.Polygon([ast.literal_eval(coords)])
    res = [_process(x, geom) for x in stack]
    return dict(results=res, count=len(res))
