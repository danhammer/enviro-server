import sys
sys.path.insert(0, 'lib')

import webapp2
import cpi
import json
import config
from datetime import datetime

TODAY = datetime.strftime(datetime.today(), '%Y-%m-%d')

with open('cpi.geojson') as f:
    GEOJSON = json.load(f)
    FIELDS = GEOJSON['features']


class CPIAnalysisHandler(webapp2.RequestHandler):

    def get(self):
        """Retrieves the CPI stats for a given bounding box."""
        try:
            # Headers
            self.response.headers.add_header(
                "Access-Control-Allow-Origin", "*"
            )
            self.response.headers['Content-Type'] = 'application/json'

            # Parameters
            xmin = self.request.get('xmin', None)
            xmax = self.request.get('xmax', None)
            ymin = self.request.get('ymin', None)
            ymax = self.request.get('ymax', None)
            bbox = dict(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
            begin = self.request.get('begin', '2000-01-01')
            end = self.request.get('end', TODAY)

            # Response
            self.response.write(json.dumps(cpi.cpi_calc(bbox, begin, end)))

        except Exception, e:
            res = json.dumps(
                {
                    "message": "error",
                    "details": str(e)
                }
            )
            self.response.write(res)


class PlotRetrieval(webapp2.RequestHandler):

    def get(self):
        """Retrieves the CPI stats for a given plot, specified by the unique
        CartoDB identifier"""
        try:
            # Headers
            self.response.headers.add_header(
                "Access-Control-Allow-Origin", "*"
            )
            self.response.headers['Content-Type'] = 'application/json'

            # Parameters
            i = int(self.request.get('id'))
            begin = self.request.get('begin', '2000-01-01')
            end = self.request.get('end', TODAY)

            # Reformat parameters
            [field] = [x for x in FIELDS if x['properties']['cartodb_id'] == i]
            [[coords]] = field['geometry']['coordinates']
            xs = map(lambda x: x[0], coords)
            ys = map(lambda x: x[1], coords)
            bbox = dict(
                xmin=min(xs),
                xmax=max(xs),
                ymin=min(ys),
                ymax=max(ys)
            )

            # Response
            self.response.write(json.dumps(cpi.cpi_calc(bbox, begin, end)))

        except Exception, e:
            res = json.dumps(
                {
                    "message": "error",
                    "details": str(e)
                }
            )
            self.response.write(res)


handlers = webapp2.WSGIApplication([
    ('/api/poly', PlotRetrieval),
    ('/api/plot', PlotRetrieval),
], debug=True)
