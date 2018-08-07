import dash

import json

import plotly

class DashServerless(dash.Dash):

  # TODO - Update nomenclature.
  # "Parents" and "Children" should refer to the DOM tree
  # and not the dependency tree.
  # The dependency tree should use the nomenclature
  # "observer" and "controller".
  # "observers" listen for changes from their "controllers". For example,
  # if a graph depends on a dropdown, the graph is the "observer" and the
  # dropdown is a "controller". In this case the graph's "dependency" is
  # the dropdown.
  # TODO - Check this map for recursive or other ill-defined non-tree
  # relationships
  # pylint: disable=dangerous-default-value
  def callback(self, output, inputs=[], state=[], events=[]):
      self._validate_callback(output, inputs, state, events)

      callback_id = '{}.{}'.format(
          output.component_id, output.component_property
      )
      self.callback_map[callback_id] = {
          'inputs': [
              {'id': c.component_id, 'property': c.component_property}
              for c in inputs
          ],
          'state': [
              {'id': c.component_id, 'property': c.component_property}
              for c in state
          ],
          'events': [
              {'id': c.component_id, 'event': c.component_event}
              for c in events
          ]
      }

      def wrap_func(func):
          @wraps(func)
          def add_context(*args, **kwargs):

              output_value = func(*args, **kwargs)
              response = {
                  'response': {
                      'props': {
                          output.component_property: output_value
                      }
                  }
              }

              return json.dumps(response, cls=plotly.utils.PlotlyJSONEncoder)

          self.callback_map[callback_id]['callback'] = add_context

          return add_context

      return wrap_func


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

    return self.callback_map[target_id]['callback'](*args), cls=plotly.utils.PlotlyJSONEncoder)