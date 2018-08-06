import dash

import json

import plotly

class DashServerless(dash.Dash):

  def index_handler(self):
    return self.index()

  def serve_layout_handler(self):
    layout = self._layout_value()
    return  json.dumps(layout, cls=plotly.utils.PlotlyJSONEncoder)

  def dependencies_handler(self):
    return json.dumps([
            {
                'output': {
                    'id': k.split('.')[0],
                    'property': k.split('.')[1]
                },
                'inputs': v['inputs'],
                'state': v['state'],
                'events': v['events']
            } for k, v in list(self.callback_map.items())
        ])

  def dispatch_handler(self, body):
    inputs = body.get('inputs', [])
    state = body.get('state', [])
    output = body['output']

    target_id = '{}.{}'.format(output['id'], output['property'])
    args = []
    for component_registration in self.callback_map[target_id]['inputs']:
        args.append([
            c.get('value', None) for c in inputs if
            c['property'] == component_registration['property'] and
            c['id'] == component_registration['id']
        ][0])

    for component_registration in self.callback_map[target_id]['state']:
        args.append([
            c.get('value', None) for c in state if
            c['property'] == component_registration['property'] and
            c['id'] == component_registration['id']
        ][0])

    return self.callback_map[target_id]['callback'](*args)