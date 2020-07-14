import SwaggerUI from 'swagger-ui'
import 'swagger-ui/dist/swagger-ui.css';

const spec = require('./swagger-config.yaml');

const ui = SwaggerUI({
  spec,
  dom_id: '#swagger',
});

ui.initOAuth({
  appName: "OMWebService API Documentation",
  // See https://demo.identityserver.io/ for configuration details.
  clientId: 'implicit'
});
